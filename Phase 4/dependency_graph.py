"""
Phase 4: Dependency Graph and Propagation
Implements Section 4 of the Dynamic Epistemic Decay Framework

Key principle: Stability is an emergent property of the dependency graph,
not a property of individual facts.

effective_decay(v) = own_decay(v) + Σ propagate(u→v) for all ancestors(v)

Edge types and transmission coefficients:
- Logical: 1.0 (full transmission)
- Empirical: weight × 0.6  
- Analogical: weight × 0.2
- Historical: ~0.0-0.05 (causally sealed)
"""

import networkx as nx
from typing import Dict, List, Set, Tuple, Optional
from enum import Enum
import numpy as np


class EdgeType(Enum):
    """Types of dependency edges with different transmission properties."""
    LOGICAL = "logical"           # Full transmission (1.0)
    EMPIRICAL = "empirical"       # Partial transmission (0.6)
    ANALOGICAL = "analogical"     # Weak transmission (0.2)
    HISTORICAL = "historical"     # Minimal transmission (0.05)
    DEFINITIONAL = "definitional" # Full transmission (1.0)


class DecayType(Enum):
    """Four decay dimensions from framework."""
    TEMPORAL = "temporal"         # λt: Exponential time-based
    PARADIGM = "paradigm"         # λp: Step function validity
    UNCERTAINTY = "uncertainty"   # λu: Bayesian confidence
    DEPENDENCY = "dependency"     # λd: Graph-propagated


# Transmission coefficients by edge type
TRANSMISSION_COEFFICIENTS = {
    EdgeType.LOGICAL: 1.0,      # If axiom fails, theorem fails fully
    EdgeType.EMPIRICAL: 0.6,    # Evidence weakening reduces confidence proportionally
    EdgeType.ANALOGICAL: 0.2,   # Analogy breaking triggers review, not immediate failure
    EdgeType.HISTORICAL: 0.05,  # Past events causally sealed from future changes
    EdgeType.DEFINITIONAL: 1.0, # Definitions propagate fully
}


class KnowledgeNode:
    """
    A node in the knowledge dependency graph.
    
    Attributes:
        id: Unique identifier
        content: Text content of the fact
        decay_vector: {temporal, paradigm, uncertainty, dependency}
        confidence: Current confidence level
        source_quality: Quality of source (affects propagation)
    """
    
    def __init__(self, node_id: str, content: str, 
                 temporal_decay: float = 0.0,
                 paradigm_scope: Set[str] = None,
                 uncertainty: float = 1.0):
        self.id = node_id
        self.content = content
        self.decay_vector = {
            DecayType.TEMPORAL: temporal_decay,
            DecayType.PARADIGM: paradigm_scope or set(),
            DecayType.UNCERTAINTY: uncertainty,
            DecayType.DEPENDENCY: 0.0  # Computed from graph
        }
        self.confidence = uncertainty
        self.source_quality = 1.0
    
    def __repr__(self):
        return f"KnowledgeNode({self.id}, conf={self.confidence:.2f})"


class DependencyGraph:
    """
    Knowledge dependency graph with typed edges and decay propagation.
    
    Graph structure:
    - Nodes: KnowledgeNode objects with decay vectors
    - Edges: Typed dependencies with weights and transmission coefficients
    
    Key operations:
    - add_dependency(): Add typed edge between facts
    - compute_effective_decay(): Propagate decay through graph
    - get_stability_score(): Compute node stability from graph topology
    """
    
    def __init__(self):
        """Initialize empty dependency graph."""
        self.graph = nx.DiGraph()
        self._node_registry: Dict[str, KnowledgeNode] = {}
    
    def add_node(self, node: KnowledgeNode):
        """Add knowledge node to graph."""
        self.graph.add_node(node.id, data=node)
        self._node_registry[node.id] = node
    
    def add_dependency(self, source_id: str, target_id: str, 
                      edge_type: EdgeType, weight: float = 1.0,
                      metadata: Dict = None):
        """
        Add typed dependency edge.
        
        Args:
            source_id: Node that target depends on
            target_id: Node that depends on source
            edge_type: Type of dependency (logical, empirical, etc.)
            weight: Edge weight (0-1), affects transmission
            metadata: Optional edge metadata
        """
        transmission = TRANSMISSION_COEFFICIENTS[edge_type] * weight
        
        self.graph.add_edge(
            source_id, 
            target_id,
            edge_type=edge_type,
            weight=weight,
            transmission=transmission,
            metadata=metadata or {}
        )
    
    def get_node(self, node_id: str) -> Optional[KnowledgeNode]:
        """Retrieve node by ID."""
        return self._node_registry.get(node_id)
    
    def propagate_decay(self, source_id: str, depth: int = 0, 
                       max_depth: int = 10) -> Dict[str, float]:
        """
        Propagate decay from source node through dependency graph.
        
        Uses exponential depth dampening: deeper dependencies contribute
        exponentially less but never zero.
        
        propagate(u→v, depth) = decay_delta(u) × transmission × weight × e^(-depth)
        
        Args:
            source_id: Starting node for propagation
            depth: Current depth (internal recursion parameter)
            max_depth: Maximum propagation depth
        
        Returns:
            Dict mapping node_id → propagated_decay_contribution
        """
        if depth >= max_depth:
            return {}
        
        source_node = self.get_node(source_id)
        if not source_node:
            return {}
        
        # Get source node's own decay
        source_decay = source_node.decay_vector[DecayType.TEMPORAL]
        
        propagation_map = {}
        
        # Propagate to all dependent nodes (outgoing edges)
        for target_id in self.graph.successors(source_id):
            edge_data = self.graph.edges[source_id, target_id]
            transmission = edge_data['transmission']
            
            # Exponential depth dampening
            depth_damping = np.exp(-depth * 0.5)  # 0.5 is dampening factor
            
            # Compute propagated decay contribution
            propagated = source_decay * transmission * depth_damping
            
            propagation_map[target_id] = propagation_map.get(target_id, 0.0) + propagated
            
            # Recursive propagation (with incremented depth)
            downstream = self.propagate_decay(target_id, depth + 1, max_depth)
            for node, decay in downstream.items():
                propagation_map[node] = propagation_map.get(node, 0.0) + decay
        
        return propagation_map
    
    def compute_effective_decay(self, node_id: str) -> float:
        """
        Compute effective decay including graph propagation.
        
        effective_decay(v) = own_decay(v) + Σ propagate(u→v) for all ancestors
        
        Args:
            node_id: Node to compute effective decay for
        
        Returns:
            Total effective decay rate
        """
        node = self.get_node(node_id)
        if not node:
            return 0.0
        
        own_decay = node.decay_vector[DecayType.TEMPORAL]
        
        # Sum propagated decay from all ancestors (incoming edges)
        propagated_decay = 0.0
        for ancestor_id in self.graph.predecessors(node_id):
            edge_data = self.graph.edges[ancestor_id, node_id]
            transmission = edge_data['transmission']
            
            ancestor_node = self.get_node(ancestor_id)
            if ancestor_node:
                ancestor_decay = ancestor_node.decay_vector[DecayType.TEMPORAL]
                propagated_decay += ancestor_decay * transmission
        
        effective_decay = own_decay + propagated_decay
        
        # Update node's dependency decay component
        node.decay_vector[DecayType.DEPENDENCY] = propagated_decay
        
        return effective_decay
    
    def compute_stability_score(self, node_id: str) -> Dict[str, any]:
        """
        Compute stability score from graph topology.
        
        Stability(v) = own_stability(v) × graph_stability(v)
        
        own_stability(v) = 1 / (1 + λt + λu)
        graph_stability(v) = product of depth-weighted transmissions from ancestors
        
        Returns:
            {
                "own_stability": float,
                "graph_stability": float,
                "total_stability": float,
                "fan_in": int,  # Number of dependencies (robustness indicator)
                "fan_out": int,  # Number of dependents (cascade risk indicator)
                "is_bridge": bool,  # Bridge node detection
                "effective_decay": float
            }
        """
        node = self.get_node(node_id)
        if not node:
            return {"total_stability": 0.0}
        
        # Own stability from decay rates
        temporal_decay = node.decay_vector[DecayType.TEMPORAL]
        uncertainty_decay = 1.0 - node.decay_vector[DecayType.UNCERTAINTY]
        
        own_stability = 1.0 / (1.0 + temporal_decay + uncertainty_decay)
        
        # Graph stability from dependencies
        fan_in = self.graph.in_degree(node_id)
        fan_out = self.graph.out_degree(node_id)
        
        # High fan-in = robustness (multiple independent supports)
        # Compute average transmission from ancestors
        if fan_in > 0:
            total_transmission = 0.0
            for ancestor_id in self.graph.predecessors(node_id):
                edge_data = self.graph.edges[ancestor_id, node_id]
                total_transmission += edge_data['transmission']
            avg_transmission = total_transmission / fan_in
            graph_stability = avg_transmission * (1.0 + np.log(fan_in + 1))  # Log bonus for multiple supports
        else:
            graph_stability = 1.0  # No dependencies = fully stable from graph perspective
        
        total_stability = own_stability * graph_stability
        
        # Bridge node detection (simplified: high betweenness centrality)
        try:
            betweenness = nx.betweenness_centrality(self.graph)[node_id]
            is_bridge = betweenness > 0.1
        except:
            is_bridge = False
        
        effective_decay = self.compute_effective_decay(node_id)
        
        return {
            "own_stability": own_stability,
            "graph_stability": graph_stability,
            "total_stability": total_stability,
            "fan_in": fan_in,
            "fan_out": fan_out,
            "is_bridge": is_bridge,
            "effective_decay": effective_decay
        }
    
    def detect_cascade_risk(self, node_id: str, threshold: float = 0.5) -> List[str]:
        """
        Detect nodes at risk of cascade failure if given node decays.
        
        Args:
            node_id: Source node to simulate decay
            threshold: Propagated decay threshold for "at risk"
        
        Returns:
            List of node IDs at cascade risk
        """
        propagation = self.propagate_decay(node_id)
        
        at_risk = []
        for target_id, propagated_decay in propagation.items():
            if propagated_decay >= threshold:
                at_risk.append(target_id)
        
        return at_risk
    
    def export_graph_statistics(self) -> Dict[str, any]:
        """Export graph topology statistics."""
        return {
            "total_nodes": self.graph.number_of_nodes(),
            "total_edges": self.graph.number_of_edges(),
            "edge_type_distribution": self._count_edge_types(),
            "is_dag": nx.is_directed_acyclic_graph(self.graph),
            "has_cycles": not nx.is_directed_acyclic_graph(self.graph),
            "strongly_connected_components": nx.number_strongly_connected_components(self.graph),
        }
    
    def _count_edge_types(self) -> Dict[str, int]:
        """Count edges by type."""
        counts = {et.value: 0 for et in EdgeType}
        for _, _, data in self.graph.edges(data=True):
            edge_type = data.get('edge_type')
            if edge_type:
                counts[edge_type.value] += 1
        return counts


# Test example
if __name__ == "__main__":
    print("=" * 80)
    print("DEPENDENCY GRAPH PROPAGATION TEST")
    print("=" * 80)
    print()
    
    # Build test graph
    graph = DependencyGraph()
    
    # Mathematical foundation (zero decay)
    axiom = KnowledgeNode("axiom_addition", "Addition is defined", 
                          temporal_decay=0.0, uncertainty=1.0)
    graph.add_node(axiom)
    
    # Theorem depending on axiom (logical dependency)
    theorem = KnowledgeNode("theorem_2plus2", "2+2=4", 
                           temporal_decay=0.0, uncertainty=1.0)
    graph.add_node(theorem)
    graph.add_dependency("axiom_addition", "theorem_2plus2", EdgeType.LOGICAL)
    
    # Empirical observation
    observation = KnowledgeNode("obs_gravity", "Objects fall at 9.8 m/s²",
                               temporal_decay=0.0001, uncertainty=0.95)
    graph.add_node(observation)
    
    # Theory based on observation (empirical dependency)
    theory = KnowledgeNode("theory_newton", "F=ma explains motion",
                          temporal_decay=0.0002, uncertainty=0.9)
    graph.add_node(theory)
    graph.add_dependency("obs_gravity", "theory_newton", EdgeType.EMPIRICAL, weight=0.8)
    
    # Application based on theory (empirical dependency)
    application = KnowledgeNode("app_rocket", "Rocket equation from F=ma",
                               temporal_decay=0.001, uncertainty=0.85)
    graph.add_node(application)
    graph.add_dependency("theory_newton", "app_rocket", EdgeType.EMPIRICAL, weight=0.9)
    
    # Test stability computation
    for node_id in ["axiom_addition", "theorem_2plus2", "theory_newton", "app_rocket"]:
        stability = graph.compute_stability_score(node_id)
        print(f"{node_id}:")
        print(f"  Own stability: {stability['own_stability']:.3f}")
        print(f"  Graph stability: {stability['graph_stability']:.3f}")
        print(f"  Total stability: {stability['total_stability']:.3f}")
        print(f"  Fan-in: {stability['fan_in']}, Fan-out: {stability['fan_out']}")
        print(f"  Effective decay: {stability['effective_decay']:.6f}")
        print()
    
    # Test cascade detection
    print("Cascade risk from 'obs_gravity' decay:")
    at_risk = graph.detect_cascade_risk("obs_gravity", threshold=0.00005)
    print(f"  Nodes at risk: {at_risk}")
    print()
    
    print("Graph statistics:")
    stats = graph.export_graph_statistics()
    for key, value in stats.items():
        print(f"  {key}: {value}")
