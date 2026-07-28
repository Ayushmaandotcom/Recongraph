import time
from typing import Sequence, Any
from recongraph.domain.records import PurchaseRecord, GSTRecord
from recongraph.matching.reference_evidence import ReferenceCorpusProfile, ReferenceEvidenceContext, ReferenceEvidencePolicy
from recongraph.graph.decision import DecisionPolicy, DecisionEngine, DecisionAction
from recongraph.graph.candidate import CandidateGraphBuilder, build_purchase_urn, build_gst_urn
from recongraph.candidate_generation.generator import CandidateGenerator
from recongraph.graph.algorithms import extract_connected_components
from recongraph.graph.search import HypothesisSearcher
from recongraph.graph.evaluator import HypothesisEvaluator
from recongraph.benchmark.models import (
    BenchmarkReport, DatasetMetadata, DecisionStatistics, SearchStatistics,
    EvidenceStatistics, ConfidenceDistribution, TimingStatistics
)

class BenchmarkRunner:
    """Executes the pipeline purely as an observer to construct a benchmark report."""
    def __init__(
        self,
        dataset_id: str,
        purchases: Sequence[PurchaseRecord],
        gsts: Sequence[GSTRecord],
        providers: list[Any],
        decision_policy: DecisionPolicy,
    ):
        self.dataset_id = dataset_id
        self.purchases = purchases
        self.gsts = gsts
        self.providers = providers
        self.decision_policy = decision_policy

    def run(self) -> BenchmarkReport:
        t0 = time.perf_counter()
        
        # 1. Candidate Generation
        gen_t0 = time.perf_counter()
        
        generator = CandidateGenerator(self.providers)
        edges = list(generator.generate(self.purchases, self.gsts))
        candidate_generation_ms = (time.perf_counter() - gen_t0) * 1000.0
        
        # 2. Graph Building
        graph_t0 = time.perf_counter()
        graph_builder = CandidateGraphBuilder()
        for p in self.purchases:
            graph_builder.add_node(build_purchase_urn(p.record_id), p)
        for g in self.gsts:
            graph_builder.add_node(build_gst_urn(g.record_id), g)
        for e in edges:
            graph_builder.add_candidate_edge(
                build_purchase_urn(e.purchase.record_id),
                build_gst_urn(e.gst_record.record_id),
                e.shared_blocking_keys
            )
        graph = graph_builder.build()
        graph_building_ms = (time.perf_counter() - graph_t0) * 1000.0
        
        # 3. Components & Search & Eval & Decisions
        components = list(extract_connected_components(graph))
        searcher = HypothesisSearcher()
        from recongraph.matching.pair_scorers import PURCHASE_TO_GST_POLICY
        evaluator = HypothesisEvaluator(self.providers, PURCHASE_TO_GST_POLICY)
        engine = DecisionEngine(self.decision_policy)
        
        max_comp_size = 0
        total_comp_nodes = 0
        total_hypotheses_evaluated = 0
        
        actions = {
            DecisionAction.AUTO_MATCH: 0,
            DecisionAction.REVIEW_AMBIGUOUS: 0,
            DecisionAction.REVIEW_WEAK: 0,
            DecisionAction.NO_MATCH: 0
        }
        bins = {f"0.{i}-0.{i+1}": 0 for i in range(10)}
        bins["1.0"] = 0
        
        search_time = 0.0
        decision_time = 0.0
        
        for comp in components:
            size = len(comp.graph.nodes)
            total_comp_nodes += size
            if size > max_comp_size:
                max_comp_size = size
            
            s_t0 = time.perf_counter()
            hypotheses = searcher.search(comp)
            evaluated = [evaluator.evaluate(graph, h) for h in hypotheses]
            total_hypotheses_evaluated += len(evaluated)
            search_time += (time.perf_counter() - s_t0)
            
            for eh in evaluated:
                score = eh.score
                if score >= 1.0:
                    bins["1.0"] += 1
                else:
                    bucket = int(score * 10)
                    bins[f"0.{bucket}-0.{bucket+1}"] += 1
            
            d_t0 = time.perf_counter()
            decision = engine.decide(evaluated)
            actions[decision.action] += 1
            decision_time += (time.perf_counter() - d_t0)
            
        search_evaluation_ms = search_time * 1000.0
        decision_ms = decision_time * 1000.0
        total_runtime_ms = (time.perf_counter() - t0) * 1000.0
        
        num_p = len(self.purchases)
        num_g = len(self.gsts)
        max_possible_edges = num_p * num_g
        reduction_ratio = 1.0 - (len(edges) / max_possible_edges) if max_possible_edges > 0 else 0.0
        avg_comp_size = total_comp_nodes / len(components) if components else 0.0

        return BenchmarkReport(
            dataset_metadata=DatasetMetadata(self.dataset_id, num_p, num_g),
            decision_statistics=DecisionStatistics(
                auto_match_count=actions[DecisionAction.AUTO_MATCH],
                review_ambiguous_count=actions[DecisionAction.REVIEW_AMBIGUOUS],
                review_weak_count=actions[DecisionAction.REVIEW_WEAK],
                no_match_count=actions[DecisionAction.NO_MATCH]
            ),
            search_statistics=SearchStatistics(
                candidate_edges=len(edges),
                components_extracted=len(components),
                max_component_size=max_comp_size,
                avg_component_size=avg_comp_size,
                candidate_reduction_ratio=reduction_ratio,
                total_hypotheses_evaluated=total_hypotheses_evaluated
            ),
            evidence_statistics=EvidenceStatistics({}),
            confidence_distribution=ConfidenceDistribution(bins),
            timing_statistics=TimingStatistics(
                total_runtime_ms=total_runtime_ms,
                candidate_generation_ms=candidate_generation_ms,
                graph_building_ms=graph_building_ms,
                search_evaluation_ms=search_evaluation_ms,
                decision_ms=decision_ms
            )
        )

def execute_reconbench(size: int = 1000, enable_faf: bool = False, auto_match_threshold: float = 0.85, ambiguity_margin: float = 0.05) -> int:
    import json
    from recongraph.synthetic.reconbench import generate_reconbench_dataset
    from recongraph.benchmark.evaluator import evaluate_results
    from recongraph.benchmark.faf import generate_faf_report
    from recongraph.plugins.core_providers import FinancialEvidenceProvider, TemporalEvidenceProvider, TaxEvidenceProvider, VendorEvidenceProvider, ReferenceEvidenceProvider
    from recongraph.matching.reference_evidence import ReferenceCorpusProfile, ReferenceEvidenceContext, ReferenceEvidencePolicy
    from recongraph.domain.vendor.context import VendorIdentityContext, VendorCorpusProfile
    from recongraph.engine import ReconGraphEngine
    from recongraph.matching.pair_scorers import PURCHASE_TO_GST_POLICY
    from recongraph.graph.decision import DecisionPolicy
    
    print(f"Generating ReconBench dataset with {size} scenarios...")
    scenarios = generate_reconbench_dataset(size=size)
    
    # We need basic contexts
    corpus_profile = ReferenceCorpusProfile(reference_count=1, normalized_reference_frequency={'dummy': 1}, numeric_token_document_frequency={})
    ref_context = ReferenceEvidenceContext(corpus_profile, ReferenceEvidencePolicy())
    vendor_context = VendorIdentityContext(
        corpus_profile=VendorCorpusProfile(corpus_size=1, token_document_frequencies={}, digest="1"),
        interpreter_policy_version="1.0.0",
        fuzzy_minimum_length=6,
        fuzzy_threshold=0.85
    )
    
    providers = [
        FinancialEvidenceProvider(),
        TemporalEvidenceProvider(),
        TaxEvidenceProvider(),
        VendorEvidenceProvider(vendor_context),
        ReferenceEvidenceProvider(ref_context)
    ]
    from recongraph.config import ReconGraphConfig, DecisionConfig, DecisionMode
    config = ReconGraphConfig(decision_config=DecisionConfig(
        decision_mode=DecisionMode.LEGACY,
        policy=DecisionPolicy(auto_match_threshold=auto_match_threshold, ambiguity_margin=ambiguity_margin)
    ))
    engine = ReconGraphEngine(
        config=config,
        providers=providers
    )
    
    results = []
    print(f"Executing engine against {size} scenarios...")
    
    for spec in scenarios:
        # Resolve mutations
        purchases = list(spec.base_purchases)
        gsts = list(spec.base_gsts)
        for idx, op in spec.purchase_mutations:
            purchases[idx] = op.apply(purchases[idx])
        for idx, op in spec.gst_mutations:
            gsts[idx] = op.apply(gsts[idx])
            
        result = engine.reconcile(purchases, gsts)
        results.append((result, spec.expected_outcome))
        
        if enable_faf:
            from recongraph.graph.decision import DecisionAction
            matched = len(result.auto_matches) > 0
            reviewed = len(result.review_packets) > 0
            
            expected = spec.expected_outcome.expected_decision
            actual = DecisionAction.AUTO_MATCH if matched else (DecisionAction.REVIEW_WEAK if reviewed else DecisionAction.NO_MATCH)
            
            # Identify Failure: (simplistic check for FAF)
            if expected == DecisionAction.AUTO_MATCH and not matched:
                generate_faf_report(spec, purchases, gsts, result, actual)
            elif expected != DecisionAction.AUTO_MATCH and matched:
                generate_faf_report(spec, purchases, gsts, result, actual)
        
    print("Evaluating metrics...")
    metrics = evaluate_results(results)
    
    print("\n================ ReconBench Results ================")
    print(f"Total Scenarios:    {metrics.total_scenarios}")
    print(f"True Positives:     {metrics.true_positives}")
    print(f"False Positives:    {metrics.false_positives}")
    print(f"False Negatives:    {metrics.false_negatives}")
    print(f"Precision:          {metrics.precision:.4f}")
    print(f"Recall:             {metrics.recall:.4f}")
    print(f"Review Rate:        {metrics.review_rate:.2%}")
    print(f"Exact Match Rate:   {metrics.exact_match_rate:.2%}")
    print("==================================================\n")
    
    # Return 0 on success (or if precision/recall are decent), 1 on catastrophic failure
    return 0 if metrics.precision > 0.0 else 1

