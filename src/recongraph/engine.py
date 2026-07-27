import time
import hashlib
from datetime import datetime, timezone
from typing import Sequence, Iterable, Any
from dataclasses import dataclass, field

from recongraph.config import ReconGraphConfig
from recongraph.plugins.provider import EvidenceProvider
from recongraph.domain.records import PurchaseRecord, GSTRecord
from recongraph.graph.decision import DecisionAction, DecisionEngine, ReconciliationDecision
from recongraph.candidate_generation.generator import CandidateGenerator
from recongraph.graph.candidate import CandidateGraphBuilder, build_purchase_urn, build_gst_urn
from recongraph.graph.algorithms import extract_connected_components
from recongraph.graph.search import HypothesisSearcher
from recongraph.graph.evaluator import HypothesisEvaluator
from recongraph.graph.review import ReviewPacketBuilder, ReviewPacket
from recongraph.graph.trace import DecisionTrace, TraceEvent, TraceStage
from recongraph.graph.explainability import ExplanationBuilder
from recongraph.errors import ReconciliationFallbackError
from recongraph.config import DecisionMode
from recongraph.graph.differential import DifferentialResult, DifferenceType
from recongraph.graph.decision import FusionDecisionEngine
from recongraph.graph.fusion import EvidenceGraph, FusionNode
from recongraph.graph.propagation import SemanticPropagator
from recongraph.graph.fusion_result import FusionResult
from recongraph.plugins.provider_v2 import EvidenceContributionV2

@dataclass(frozen=True)
class ReconciliationResult:
    auto_matches: list[ReconciliationDecision]
    review_packets: list[ReviewPacket]
    traces: list[DecisionTrace]
    engine_version: str
    differential_results: list['DifferentialResult'] = field(default_factory=list)
    
class ReconGraphEngine:
    try:
        import importlib.metadata
        VERSION = importlib.metadata.version("recongraph")
    except Exception:
        VERSION = "0.9.0"

    def __init__(self, config: ReconGraphConfig, providers: Sequence[EvidenceProvider]):
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
        evaluator = HypothesisEvaluator(self.providers, self.config.decision_config.relationship_policy)
        decision_engine = DecisionEngine(self.config.decision_config.policy)
        explanation_builder = ExplanationBuilder()
        packet_builder = ReviewPacketBuilder()
        
        auto_matches = []
        review_packets = []
        traces = []
        differential_results = []
        
        try:
            for comp in components:
                hypotheses = searcher.search(comp)
                evaluated = [evaluator.evaluate(graph, h) for h in hypotheses]
                
                # Baseline Legacy Evaluation
                t0 = time.time()
                decision = decision_engine.decide(evaluated)
                legacy_time = time.time() - t0
                
                # Shadow/Fusion Evaluation
                if self.config.decision_config.decision_mode in (DecisionMode.SHADOW, DecisionMode.FUSION):
                    try:
                        t1 = time.time()
                        # Build EvidenceGraph from EvaluatedHypotheses
                        evidence_graph = EvidenceGraph()
                        for h in evaluated:
                            contributions = h.supporting_evidence.contributions
                            for provider_name, contrib in contributions.items():
                                # We must convert EvidenceContribution to EvidenceContributionV2
                                contrib_v2: EvidenceContributionV2[Any] = EvidenceContributionV2(
                                    provider_name=contrib.provider_name,
                                    score=contrib.score,
                                    violations=contrib.violations,
                                    metadata=contrib.metadata
                                )
                                node = FusionNode.from_contribution(contrib_v2)
                                evidence_graph.add_node(node)
                                
                        propagated_nodes = SemanticPropagator.propagate(evidence_graph)
                        
                        fusion_result = FusionResult.from_propagated_graph(
                            nodes=propagated_nodes,
                            dependency_groups=[], # Omitted for brevity
                            missingness={},
                            coverage=decision.selected_hypothesis.coverage if decision.selected_hypothesis else 0.0
                        )
                        
                        fusion_engine = FusionDecisionEngine()
                        fusion_decision = fusion_engine.decide(fusion_result, decision.selected_hypothesis)
                        fusion_time = time.time() - t1
                        
                        if self.config.decision_config.decision_mode == DecisionMode.FUSION:
                            decision = fusion_decision
                    except Exception as e:
                        # Shadow failure must NEVER break the legacy pipeline
                        if self.config.decision_config.decision_mode == DecisionMode.FUSION:
                            raise e # Unless explicitly in FUSION mode
                            
                # 7E: Trace Versioning (always generated)
                trace_id = DecisionTrace.compute_identity(
                    engine_version=self.VERSION,
                    config_hash=self.config_hash,
                    component_nodes=frozenset(comp.graph.nodes.keys()),
                    decision=decision
                )
                
                trace = DecisionTrace(
                    trace_id=trace_id,
                    engine_version=self.VERSION,
                    config_hash=self.config_hash,
                    events=()
                )
                traces.append(trace)
                
                # Explanation Generation
                legacy_explanation = explanation_builder.build(decision)
                fusion_explanation = None
                
                if 'evidence_graph' in locals() and 'fusion_result' in locals() and evidence_graph and fusion_result:
                    from recongraph.graph.explanation_generator import ExplanationGenerator
                    explanation_generator = ExplanationGenerator(trace, evidence_graph, fusion_result, decision)
                    fusion_explanation = explanation_generator.generate()
                    
                if self.config.decision_config.decision_mode in (DecisionMode.SHADOW, DecisionMode.FUSION) and 'fusion_decision' in locals():
                    diff_result = DifferentialResult.classify(
                        legacy=decision.action if self.config.decision_config.decision_mode == DecisionMode.FUSION else decision.action,
                        fusion=fusion_decision.action,
                        perf={"legacy_ms": legacy_time * 1000, "fusion_ms": fusion_time * 1000},
                        legacy_exp={"summary": legacy_explanation} if legacy_explanation else None,
                        fusion_exp=fusion_explanation.executive_summary if fusion_explanation else None
                    )
                    differential_results.append(diff_result)
        
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
            engine_version=self.VERSION,
            differential_results=differential_results
        )
