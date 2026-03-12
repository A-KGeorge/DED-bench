"""
Phase 3: Graph Evaluation Script

Evaluates graph-only performance on annotated test cases.
Loads graph_facts.json, builds knowledge graph, runs queries through graph matching.

Usage:
    python evaluate_graph.py
"""

import json
import sys
from pathlib import Path
from datetime import datetime

sys.path.append('Phase 3')

from knowledge_graph import TemporalKnowledgeGraph
from graph_matching import compute_graph_alignment


def load_graph_facts(facts_file: str = "Phase 3/graph_facts.json") -> dict:
    """Load annotated graph facts from JSON file."""
    with open(facts_file, 'r') as f:
        return json.load(f)


def build_knowledge_graph(facts: dict) -> TemporalKnowledgeGraph:
    """
    Build knowledge graph from all annotated cases.
    
    Args:
        facts: Dict from graph_facts.json
        
    Returns:
        TemporalKnowledgeGraph with all facts loaded
    """
    graph = TemporalKnowledgeGraph()
    
    # Process each case
    for case_id, case_data in facts.items():
        if case_id == "_metadata":
            continue
        
        # Add all role facts
        for role_fact in case_data.get("roles", []):
            graph.add_role_fact(
                entity=role_fact["entity"],
                role=role_fact["role"],
                org=role_fact["org"],
                start_date=role_fact["start_date"],
                end_date=role_fact.get("end_date")
            )
        
        # Add succession links
        for succession in case_data.get("successions", []):
            graph.add_succession(
                predecessor_entity=succession["predecessor"],
                successor_entity=succession["successor"],
                role=succession["role"],
                org=succession["org"],
                transition_date=succession["transition_date"]
            )
    
    return graph


def evaluate_graph_only(facts_file: str = "Phase 3/graph_facts.json", verbose: bool = True) -> dict:
    """
    Evaluate graph-only performance on test cases.
    
    Args:
        facts_file: Path to graph_facts.json
        verbose: Print detailed results
        
    Returns:
        Dict with evaluation results
    """
    facts = load_graph_facts(facts_file)
    graph = build_knowledge_graph(facts)
    
    if verbose:
        print("="*80)
        print("GRAPH-ONLY EVALUATION")
        print("="*80)
        print()
        print(f"Loaded {len(facts) - 1} test cases from {facts_file}")  # -1 for _metadata
        print(f"Knowledge graph: {graph.graph.number_of_nodes()} nodes, {graph.graph.number_of_edges()} edges")
        print()
    
    results = []
    correct_count = 0
    
    # Evaluate each case
    for case_id, case_data in facts.items():
        if case_id == "_metadata":
            continue
        
        query = case_data["query"]
        expected = case_data["expected_answer"]
        challenge = case_data.get("challenge", "unknown")
        
        # Run graph matching
        graph_result = compute_graph_alignment(query, graph)
        
        matched_entity = graph_result["matched_entity"]
        match_type = graph_result["match_type"]
        score = graph_result["score"]
        
        # Check correctness
        # For counterfactual/unknown cases, accept None as correct if expected indicates null
        is_correct = (
            matched_entity == expected or 
            (("null" in expected.lower() or "unknown" in expected.lower()) and matched_entity is None)
        )
        
        if is_correct:
            correct_count += 1
        
        results.append({
            "case_id": case_id,
            "query": query,
            "expected": expected,
            "matched": matched_entity,
            "match_type": match_type,
            "score": score,
            "correct": is_correct,
            "challenge": challenge
        })
        
        if verbose:
            status = "✓" if is_correct else "✗"
            print(f"{status} {case_id} [{challenge}]")
            print(f"  Query: {query}")
            print(f"  Expected: {expected}")
            print(f"  Matched: {matched_entity} ({match_type}, score={score:.2f})")
            if not is_correct:
                print(f"  → MISMATCH!")
            print()
    
    accuracy = correct_count / len(results) if results else 0.0
    
    if verbose:
        print("="*80)
        print("SUMMARY")
        print("="*80)
        print(f"Accuracy: {correct_count}/{len(results)} ({accuracy*100:.1f}%)")
        print()
        
        # Breakdown by challenge type
        challenges = {}
        for result in results:
            challenge = result["challenge"]
            if challenge not in challenges:
                challenges[challenge] = {"total": 0, "correct": 0}
            challenges[challenge]["total"] += 1
            if result["correct"]:
                challenges[challenge]["correct"] += 1
        
        print("Breakdown by challenge type:")
        for challenge, stats in challenges.items():
            acc = stats["correct"] / stats["total"] if stats["total"] > 0 else 0.0
            print(f"  {challenge}: {stats['correct']}/{stats['total']} ({acc*100:.1f}%)")
        print()
    
    return {
        "accuracy": accuracy,
        "correct": correct_count,
        "total": len(results),
        "results": results,
        "challenge_breakdown": challenges if verbose else {}
    }


def compare_with_phase2():
    """
    Compare graph-only performance with Phase 2 results.
    
    Based on analyze_failures.py, Phase 2 failed 6/61 manual benchmark cases.
    These 6 failures should be solvable by graph matching.
    """
    print("="*80)
    print("COMPARISON WITH PHASE 2")
    print("="*80)
    print()
    
    print("Phase 2 Manual Benchmark Performance:")
    print("  Total cases: 61")
    print("  Correct: 55/61 (90.2%)")
    print("  Failures: 6/61 (9.8%)")
    print("    - Continuity cases: 2 (Amazon 2021, Netflix 2020)")
    print("    - Small gap cases: 4 (Google 2001, France 2007, Twitter 2008/2010)")
    print()
    
    print("Phase 3 Target:")
    print("  Solve all 6 Phase 2 failures via structural matching")
    print("  Plus 2 fuzzy logic failures (succession queries)")
    print("  Total: 8 cases")
    print()


def test_temporal_consistency():
    """Test that the built graph has no temporal inconsistencies."""
    facts = load_graph_facts()
    graph = build_knowledge_graph(facts)
    
    print("="*80)
    print("TEMPORAL CONSISTENCY CHECK")
    print("="*80)
    print()
    
    errors = graph.validate_temporal_consistency()
    
    if not errors:
        print("✓ Knowledge graph is temporally consistent (no overlapping roles)")
    else:
        print(f"✗ Found {len(errors)} temporal inconsistencies:")
        for error in errors:
            print(f"  - {error}")
    
    print()
    return len(errors) == 0


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Evaluate graph-only performance")
    parser.add_argument("--verbose", action="store_true", help="Print detailed results")
    parser.add_argument("--facts", default="Phase 3/graph_facts.json", help="Path to graph facts file")
    parser.add_argument("--compare", action="store_true", help="Compare with Phase 2 results")
    
    args = parser.parse_args()
    
    # Check temporal consistency
    consistent = test_temporal_consistency()
    
    if not consistent:
        print("⚠️  WARNING: Graph has temporal inconsistencies, results may be unreliable")
        print()
    
    # Run evaluation
    eval_results = evaluate_graph_only(args.facts, verbose=args.verbose or True)
    
    # Compare with Phase 2
    if args.compare or True:  # Always show comparison
        compare_with_phase2()
    
    # Final verdict
    print("="*80)
    print("PHASE 3 GRAPH EVALUATION COMPLETE")
    print("="*80)
    print()
    
    if eval_results["accuracy"] >= 0.875:  # 7/8 or better
        print(f"✅ SUCCESS: {eval_results['correct']}/{eval_results['total']} correct")
        print("Graph matching successfully handles Phase 2 failure cases!")
    else:
        print(f"⚠️  NEEDS IMPROVEMENT: {eval_results['correct']}/{eval_results['total']} correct")
        print("Some cases still failing, review graph facts or matching logic.")
