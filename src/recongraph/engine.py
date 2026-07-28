import time
import hashlib
from datetime import datetime, timezone
from typing import Sequence, Iterable, Any
from dataclasses import dataclass, field

from recongraph.config import ReconGraphConfig
from recongraph.plugins.provider import EvidenceProvider
from recongraph.domain.records import PurchaseRecord, GSTRecord
from recongraph.graph.decision import DecisionAction, ReconciliationDecision, FusionDecisionEngine
from recongraph.candidate_generation.generator import CandidateGenerator
from recongraph.graph.candidate import CandidateGraphBuilder, build_purchase_urn, build_gst_urn
from recongraph.graph.algorithms import extract_connected_components
from recongraph.graph.search import HypothesisSearcher
from recongraph.graph.evaluator import HypothesisEvaluator
from recongraph.graph.review import ReviewPacketBuilder, ReviewPacket
from recongraph.graph.trace import DecisionTrace, TraceEvent, TraceStage
from recongraph.errors import ReconciliationFallbackError
from recongraph.graph.fusion import EvidenceGraph, FusionNode
from recongraph.graph.propagation import SemanticPropagator
from recongraph.graph.fusion_result import FusionResult
from recongraph.plugins.provider_v2 import EvidenceContributionV2

try:
    from importlib.metadata import version as _get_version
    __version__ = _get_version('recongraph')
except Exception:
    __version__ = '0.9.0'


@dataclass(frozen=True)
class ReconciliationResult:
    auto_matches: list[ReconciliationDecision]
    review_packets: list[ReviewPacket]
    traces: list[DecisionTrace]
    engine_version: str
    differential_results: list['DifferentialResult'] = field(default_factory=list)
    
    def to_dict(self) -> dict[str, Any]:
        import json
        from recongraph.serialization import ReconEncoder
        return json.loads(json.dumps(self, cls=ReconEncoder))
    
class ReconGraphEngine:
    try:
        pass
    except Exception:
        # Fallback for editable installs or missing metadata.
        # Must stay in sync with pyproject.toml [project] version.
        VERSION = "0.9.0"

    def __init__(self, config: ReconGraphConfig, providers: list[EvidenceProvider]):
        self.config = config
        self.providers = tuple(providers)

    @property
    def config_hash(self) -> str:
        base_hash = str(self.config)
        digests = []
        for provider in self.providers:
            ctx = getattr(provider, "context", None)
            if ctx:
                cp = getattr(ctx, "corpus_profile", None)
                if cp and hasattr(cp, "digest"):
                    digests.append(cp.digest)
        if digests:
            base_hash += "_" + "_".join(sorted(digests))
        import hashlib
        return hashlib.md5(base_hash.encode()).hexdigest()
        
    def reconcile(self, purchases: Sequence[PurchaseRecord], gsts: Sequence[GSTRecord]) -> ReconciliationResult:
        # 1. Candidate Generation
        generator = CandidateGenerator(self.providers)
        edges = list(generator.generate(purchases, gsts))
        
        # 2. Graph Building
        graph_builder = CandidateGraphBuilder()
        for p in purchases:
            graph_builder.add_node(build_purchase_urn(p.record_id), p)
        for g in gsts:
            graph_builder.add_node(build_gst_urn(g.record_id), g)
        for e in edges:
            graph_builder.add_candidate_edge(
                build_purchase_urn(e.purchase.record_id),
                build_gst_urn(e.gst_record.record_id),
                e.shared_blocking_keys
            )
        graph = graph_builder.build()
        
        # 3. Component Extraction & Search
        components = extract_connected_components(graph)
        searcher = HypothesisSearcher()
        evaluator = HypothesisEvaluator(self.providers)
        packet_builder = ReviewPacketBuilder()
        
        auto_matches = []
        review_packets: list[Any] = []
        traces = []
        
        try:
            for comp in components:
                # OVERSIZED COMPONENT SKIP
                if len(comp.graph.edges) > 15:
                    # Treat the entire component as REVIEW_AMBIGUOUS
                    purchases_in_comp = [comp.graph.nodes[u] for u in comp.graph.nodes if str(u).startswith("urn:recongraph:purchase:")]
                    gsts_in_comp = [comp.graph.nodes[u] for u in comp.graph.nodes if str(u).startswith("urn:recongraph:gst:")]
                    review_packets.append(ReviewPacket(
                        packet_id=f"RP-SKIP-{len(review_packets)}",
                        action=DecisionAction.REVIEW_AMBIGUOUS,
                        purchases=tuple(purchases_in_comp),
                        gsts=tuple(gsts_in_comp),
                        explanation=None,
                        competitors=tuple(),
                        checklist=("Oversized component bypassed",)
                    ))
                    continue
                    
                hypotheses = searcher.search(comp)
                evaluated = [evaluator.evaluate(graph, h) for h in hypotheses]
                
                # Baseline Legacy Evaluation -> Removed in Stage 8J
                # All hypotheses evaluated will now purely build EvidenceGraphs
                
                t1 = time.time()
                fusion_decision = None
                evidence_graph = None
                fusion_result = None
                fusion_explanation = None
                
                if evaluated:
                    # Sort evaluated hypotheses to find the best candidate if needed
                    # Actually, we build an EvidenceGraph for all of them? No, we need to pick a hypothesis to fuse
                    # Or do we fuse the whole component? 
                    # The previous code iterated over evaluated hypotheses and built an EvidenceGraph from them, but wait!
                    # "for h in evaluated: contributions = h.supporting_evidence.contributions"
                    # Yes, it fused ALL hypotheses in the component into ONE graph!
                    evidence_graph = EvidenceGraph()
                    for h in evaluated:
                        contributions = h.supporting_evidence.contributions
                        for provider_name, contrib in contributions.items():
                            contrib_v2: EvidenceContributionV2[Any] = EvidenceContributionV2(
                                provider_name=contrib.provider_name,
                                score=contrib.score,
                                violations=contrib.violations,
                                metadata=contrib.metadata
                            )
                            node = FusionNode.from_contribution(contrib_v2)
                            evidence_graph.add_node(node)
                            
                    propagated_nodes = SemanticPropagator.propagate(evidence_graph)
                    
                    # We need to find the "selected_hypothesis"
                    # Since we don't have the legacy DecisionEngine, FusionDecisionEngine takes (fusion_result, legacy_selected_hypothesis)
                    # Wait, the signature of fusion_engine.decide is `def decide(self, result: FusionResult, legacy_target: EvaluatedHypothesis | None) -> ReconciliationDecision`
                    # Without legacy, we just pass None, or the one with the highest coverage.
                    best_hypothesis = max(evaluated, key=lambda x: x.coverage) if evaluated else None
                    
                    fusion_result = FusionResult.from_propagated_graph(
                        nodes=propagated_nodes,
                        dependency_groups=[], # Omitted for brevity
                        missingness={},
                        coverage=best_hypothesis.coverage if best_hypothesis else 0.0
                    )
                    
                    fusion_engine = FusionDecisionEngine()
                    fusion_decision = fusion_engine.decide(fusion_result, best_hypothesis)
                else:
                    # No hypotheses generated
                    fusion_decision = ReconciliationDecision(
                        action=DecisionAction.NO_MATCH,
                        selected_hypothesis=None,
                        competitors=()
                    )
                    
                decision = fusion_decision
                
                # 7E: Trace Versioning (always generated)
                trace_id = DecisionTrace.compute_identity(
                    engine_version=__version__,
                    config_hash=self.config_hash,
                    component_nodes=frozenset(comp.graph.nodes.keys()),
                    decision=decision
                )
                
                trace = DecisionTrace(
                    trace_id=trace_id,
                    engine_version=__version__,
                    config_hash=self.config_hash,
                    events=()
                )
                traces.append(trace)
                
                # Explanation Generation
                if evidence_graph and fusion_result:
                    from recongraph.graph.explanation_generator import ExplanationGenerator
                    explanation_generator = ExplanationGenerator(trace, evidence_graph, fusion_result, decision)
                    fusion_explanation = explanation_generator.generate()
        
                # Determine which nodes were "consumed" by the primary action
                consumed_nodes = frozenset()

                # Action Mapping
                if decision.action == DecisionAction.AUTO_MATCH:
                    auto_matches.append(decision)
                    if decision.selected_hypothesis:
                        consumed_nodes = decision.selected_hypothesis.hypothesis.matched_nodes
                elif self.config.review_config.enabled and decision.action in (DecisionAction.REVIEW_WEAK, DecisionAction.REVIEW_AMBIGUOUS):
                    packet = packet_builder.build(decision, fusion_explanation, graph)
                    if packet:
                        review_packets.append(packet)
                        
                        target_hypothesis = decision.selected_hypothesis
                        if not target_hypothesis and decision.competitors:
                            target_hypothesis = decision.competitors[0]
                        if target_hypothesis:
                            consumed_nodes = target_hypothesis.hypothesis.matched_nodes
                            
                # -------------------------------------------------------------
                # THE CONSERVATION FALLBACK (Closing the data-loss hole)
                # -------------------------------------------------------------
                # Any node in the component that was NOT consumed by the primary
                # action gets its own individual NO_MATCH packet.
                # If the action was NO_MATCH, consumed_nodes is empty, so EVERY 
                # node gets a packet.
                component_nodes = frozenset(comp.graph.nodes.keys())
                leftover_nodes = component_nodes - consumed_nodes
                
                for urn in leftover_nodes:
                    packet = packet_builder.build_single_leftover(urn, graph)
                    if packet:
                        review_packets.append(packet)
                        
        except Exception as e:
            raise ReconciliationFallbackError(f"Catastrophic failure in engine evaluation: {e}") from e
            
        return ReconciliationResult(
            auto_matches=auto_matches,
            review_packets=review_packets,
            traces=traces,
            engine_version=__version__,
            differential_results=[]
        )
