import time
import hashlib
from datetime import datetime, timezone
from typing import Sequence, Iterable
from dataclasses import dataclass

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

@dataclass(frozen=True)
class ReconciliationResult:
    auto_matches: list[ReconciliationDecision]
    review_packets: list[ReviewPacket]
    traces: list[DecisionTrace]
    engine_version: str
    
class ReconGraphEngine:
    VERSION = "1.0.0"

    def __init__(self, config: ReconGraphConfig, providers: Sequence[EvidenceProvider]):
        self.config = config
        self.providers = tuple(providers)
        
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
        
        try:
            for comp in components:
                hypotheses = searcher.search(comp)
                evaluated = [evaluator.evaluate(graph, h) for h in hypotheses]
                
                decision = decision_engine.decide(evaluated)
                explanation = explanation_builder.build(decision)
        
                # Action Mapping
                if decision.action == DecisionAction.AUTO_MATCH:
                    auto_matches.append(decision)
                elif self.config.review_config.enabled and decision.action in (DecisionAction.REVIEW_WEAK, DecisionAction.REVIEW_AMBIGUOUS):
                    packet = packet_builder.build(decision, explanation, graph)
                    if packet:
                        review_packets.append(packet)
                        
                # 7E: Trace Versioning
                trace_id = DecisionTrace.compute_identity(
                    engine_version=self.VERSION,
                    config_hash=hashlib.md5(str(self.config).encode()).hexdigest(),
                    component_nodes=frozenset(comp.graph.nodes.keys())
                )
                trace = DecisionTrace(
                    trace_id=trace_id,
                    engine_version=self.VERSION,
                    config_hash=hashlib.md5(str(self.config).encode()).hexdigest(),
                    events=tuple([
                        TraceEvent(timestamp=datetime.now(timezone.utc), stage=TraceStage.DECISION_EVALUATION, payload=decision)
                    ])
                )
                traces.append(trace)
        except Exception as e:
            raise ReconciliationFallbackError(f"Catastrophic failure in engine evaluation: {e}") from e
            
        return ReconciliationResult(
            auto_matches=auto_matches,
            review_packets=review_packets,
            traces=traces,
            engine_version=self.VERSION
        )
