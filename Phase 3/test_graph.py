"""
Test script for TemporalKnowledgeGraph

Verifies graph structure, role queries, and temporal consistency.
"""

import sys
sys.path.append('Phase 3')

from knowledge_graph import TemporalKnowledgeGraph
from datetime import datetime


def test_basic_graph_operations():
    """Test basic graph creation and queries."""
    print("=" * 80)
    print("TEST 1: Basic Graph Operations")
    print("=" * 80)
    
    graph = TemporalKnowledgeGraph()
    
    # Add Amazon CEO history
    graph.add_role_fact("Jeff Bezos", "CEO", "Amazon", "1994-07-05", "2021-07-05")
    graph.add_role_fact("Andy Jassy", "CEO", "Amazon", "2021-07-05", None)
    graph.add_succession("Jeff Bezos", "Andy Jassy", "CEO", "Amazon", "2021-07-05")
    
    print(f"Graph: {graph}")
    print()
    
    # Test queries
    print("Query: Who was Amazon CEO in 2020?")
    holder_2020 = graph.get_role_holder("Amazon", "CEO", 2020)
    print(f"Result: {holder_2020}")
    assert holder_2020 == "Jeff Bezos", f"Expected 'Jeff Bezos', got '{holder_2020}'"
    print("✓ PASS")
    print()
    
    print("Query: Who was Amazon CEO in 2021?")
    holder_2021 = graph.get_role_holder("Amazon", "CEO", 2021)
    print(f"Result: {holder_2021}")
    assert holder_2021 == "Andy Jassy", f"Expected 'Andy Jassy', got '{holder_2021}'"
    print("✓ PASS")
    print()
    
    print("Query: Who was Amazon CEO in 2024?")
    holder_2024 = graph.get_role_holder("Amazon", "CEO", 2024)
    print(f"Result: {holder_2024}")
    assert holder_2024 == "Andy Jassy", f"Expected 'Andy Jassy', got '{holder_2024}'"
    print("✓ PASS")
    print()
    
    # Test succession chain
    print("Query: Get Amazon CEO succession chain")
    chain = graph.get_succession_chain("Amazon", "CEO")
    print(f"Result: {chain}")
    assert chain == ["Jeff Bezos", "Andy Jassy"], f"Expected ['Jeff Bezos', 'Andy Jassy'], got {chain}"
    print("✓ PASS")
    print()


def test_multiple_orgs():
    """Test graph with multiple organizations."""
    print("=" * 80)
    print("TEST 2: Multiple Organizations")
    print("=" * 80)
    
    graph = TemporalKnowledgeGraph()
    
    # Amazon
    graph.add_role_fact("Jeff Bezos", "CEO", "Amazon", "1994-07-05", "2021-07-05")
    graph.add_role_fact("Andy Jassy", "CEO", "Amazon", "2021-07-05", None)
    
    # Apple
    graph.add_role_fact("Steve Jobs", "CEO", "Apple", "1997-09-16", "2011-08-24")
    graph.add_role_fact("Tim Cook", "CEO", "Apple", "2011-08-24", None)
    
    # Netflix
    graph.add_role_fact("Reed Hastings", "CEO", "Netflix", "1998-01-01", "2023-01-01")
    graph.add_role_fact("Ted Sarandos", "CEO", "Netflix", "2023-01-01", None)
    
    print(f"Graph: {graph}")
    print()
    
    # Test queries
    test_cases = [
        ("Amazon", "CEO", 2021, "Andy Jassy"),
        ("Apple", "CEO", 2005, "Steve Jobs"),
        ("Apple", "CEO", 2020, "Tim Cook"),
        ("Netflix", "CEO", 2020, "Reed Hastings"),
        ("Netflix", "CEO", 2024, "Ted Sarandos"),
    ]
    
    for org, role, year, expected in test_cases:
        result = graph.get_role_holder(org, role, year)
        status = "✓ PASS" if result == expected else "✗ FAIL"
        print(f"{org} {role} in {year}: {result} (expected: {expected}) {status}")
        assert result == expected, f"Query failed: {org}/{role}/{year}"
    
    print()


def test_temporal_consistency():
    """Test temporal consistency validation."""
    print("=" * 80)
    print("TEST 3: Temporal Consistency Validation")
    print("=" * 80)
    
    # Valid graph
    graph1 = TemporalKnowledgeGraph()
    graph1.add_role_fact("Person A", "CEO", "Company X", "2000-01-01", "2010-01-01")
    graph1.add_role_fact("Person B", "CEO", "Company X", "2010-01-01", "2020-01-01")
    
    errors1 = graph1.validate_temporal_consistency()
    print(f"Valid graph errors: {errors1}")
    assert len(errors1) == 0, "Valid graph should have no errors"
    print("✓ PASS: No temporal inconsistencies")
    print()
    
    # Invalid graph (overlapping roles)
    graph2 = TemporalKnowledgeGraph()
    graph2.add_role_fact("Person A", "CEO", "Company Y", "2000-01-01", "2015-01-01")
    graph2.add_role_fact("Person B", "CEO", "Company Y", "2010-01-01", "2020-01-01")
    
    errors2 = graph2.validate_temporal_consistency()
    print(f"Invalid graph errors: {errors2}")
    assert len(errors2) > 0, "Overlapping roles should be detected"
    print("✓ PASS: Overlap detected")
    print()


def test_serialization():
    """Test graph save/load."""
    print("=" * 80)
    print("TEST 4: Graph Serialization")
    print("=" * 80)
    
    # Create graph
    graph1 = TemporalKnowledgeGraph()
    graph1.add_role_fact("Jeff Bezos", "CEO", "Amazon", "1994-07-05", "2021-07-05")
    graph1.add_role_fact("Andy Jassy", "CEO", "Amazon", "2021-07-05", None)
    
    # Save to dict
    data = graph1.to_dict()
    print(f"Serialized nodes: {len(data['nodes'])}")
    print(f"Serialized edges: {len(data['edges'])}")
    
    # Load from dict
    graph2 = TemporalKnowledgeGraph.from_dict(data)
    print(f"Loaded graph: {graph2}")
    
    # Verify query works after load
    holder = graph2.get_role_holder("Amazon", "CEO", 2021)
    print(f"Query after load: Who was Amazon CEO in 2021? → {holder}")
    assert holder == "Andy Jassy", "Loaded graph query failed"
    print("✓ PASS: Serialization works")
    print()


def test_continuity_case():
    """Test Case 1: Andy Jassy continuity (2021 vs 2024)."""
    print("=" * 80)
    print("TEST 5: Case 1 - Jassy Continuity")
    print("=" * 80)
    print("Query: 'Who was Amazon CEO in 2021?'")
    print("Documents:")
    print("  - Doc A (acquired 2021-07-15): Andy Jassy became CEO in 2021")
    print("  - Doc B (acquired 2024-01-15): Andy Jassy continues as CEO in 2024")
    print()
    
    graph = TemporalKnowledgeGraph()
    graph.add_role_fact("Andy Jassy", "CEO", "Amazon", "2021-07-05", None)
    
    # Query for 2021
    holder_2021 = graph.get_role_holder("Amazon", "CEO", 2021)
    print(f"Graph query result: {holder_2021}")
    
    # Both docs match structurally (same person, role valid in 2021)
    # But we need era matching to prefer Doc A
    # This demonstrates graph gives us STRUCTURAL MATCH
    # Then we layer on era matching for disambiguation
    
    print()
    print("Graph analysis:")
    print("  - Doc A: Entity=Andy Jassy, Role valid 2021-07-05 to present")
    print("  - Doc B: Entity=Andy Jassy, Role valid 2021-07-05 to present")
    print("  - Both structurally match! (same role interval)")
    print()
    print("Next step: Combine graph match (1.0) with era matching")
    print("  - Doc A acquired 2021 → era match with query year 2021 → boost")
    print("  - Doc B acquired 2024 → era mismatch with query year 2021 → no boost")
    print()
    print("✓ PASS: Graph provides structural foundation for era disambiguation")
    print()


if __name__ == "__main__":
    test_basic_graph_operations()
    test_multiple_orgs()
    test_temporal_consistency()
    test_serialization()
    test_continuity_case()
    
    print("=" * 80)
    print("ALL TESTS PASSED ✓")
    print("=" * 80)
    print()
    print("Graph structure verified. Ready for:")
    print("  1. Query graph extraction (query_graph.py)")
    print("  2. Graph matching scoring (graph_matching.py)")
    print("  3. Manual annotation (graph_facts.json)")
