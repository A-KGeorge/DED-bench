"""
Dump Phase 3 knowledge graph contents to understand coverage.
"""

import sys
import os

# Ensure we're working with the correct paths
script_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(script_dir)

from knowledge_graph import TemporalKnowledgeGraph
import json

# Load graph from facts
facts_path = os.path.join(script_dir, 'graph_facts.json')
with open(facts_path, 'r') as f:
    data = json.load(f)

kg = TemporalKnowledgeGraph()

# Load all cases
for case_id, case_data in data.items():
    if case_id == "_metadata":
        continue
    
    # Load roles
    for role_data in case_data.get("roles", []):
        kg.add_role_fact(
            entity=role_data["entity"],
            role=role_data["role"],
            org=role_data["org"],
            start_date=role_data["start_date"],
            end_date=role_data.get("end_date")
        )

print("=" * 80)
print("PHASE 3 KNOWLEDGE GRAPH CONTENTS")
print("=" * 80)
print()

# Get graph structure
graph_dict = kg.to_dict()

print(f"Total nodes: {len(graph_dict['nodes'])}")
print(f"Total edges: {len(graph_dict['edges'])}")
print()

# Debug: Show raw node structure
print("=" * 80)
print("RAW NODE LIST (first 10)")
print("=" * 80)
print()
for i, node in enumerate(graph_dict['nodes'][:10]):
    print(f"Node {i}: {node}")
print()

# Group by organization - check actual keys
print("=" * 80)
print("COVERAGE BY ORGANIZATION")
print("=" * 80)
print()

orgs = {}
for node in graph_dict['nodes']:
    if node.get('type') == 'ROLE':
        org = node.get('org', 'unknown')
        if org not in orgs:
            orgs[org] = []
        orgs[org].append(node)

print("=" * 80)
print("COVERAGE BY ORGANIZATION")
print("=" * 80)
print()

for org in sorted(orgs.keys()):
    print(f"{org}:")
    roles = orgs[org]
    # Sort by start date
    roles.sort(key=lambda x: x['start_date'] if x['start_date'] else '9999')
    
    for role in roles:
        entity = role['entity']
        role_name = role['role']
        start = role['start_date'] or 'unknown'
        end = role['end_date'] or 'present'
        
        print(f"  {entity:20s} {role_name:15s} {start} → {end}")
    print()

print("=" * 80)
print("SUCCESSION CHAINS")
print("=" * 80)
print()

# Extract succession chains
for org in sorted(orgs.keys()):
    roles = orgs[org]
    if len(roles) > 1:
        print(f"{org}:")
        chain = kg.get_succession_chain(org, roles[0]['role'])
        for i, entity in enumerate(chain):
            # Find the role node to get dates
            role_node = next((r for r in roles if r['entity'] == entity), None)
            if role_node:
                start = role_node.get('start_date', 'unknown')
                end = role_node.get('end_date') or 'present'
                marker = ' [current]' if end == 'present' else ''
                print(f"  {i+1}. {entity:20s} ({start} → {end}){marker}")
        print()

print("=" * 80)
print("ENTITY INDEX")
print("=" * 80)
print()

# List all unique entities
entities = set()
for node in graph_dict['nodes']:
    if node['type'] == 'entity':
        entities.add(node['name'])

print(f"Total unique entities: {len(entities)}")
print()
for entity in sorted(entities):
    print(f"  - {entity}")

print()
print("=" * 80)
print("GRAPH STATISTICS")
print("=" * 80)
print()

# Count node types
entity_nodes = [n for n in graph_dict['nodes'] if n.get('type') in ['PERSON', 'ORG']]
role_nodes = [n for n in graph_dict['nodes'] if n.get('type') == 'ROLE']

print(f"Entity nodes: {len(entity_nodes)}")
print(f"Role nodes:   {len(role_nodes)}")
print(f"Total nodes:  {len(graph_dict['nodes'])}")
print(f"Total edges:  {len(graph_dict['edges'])}")
print()

# Coverage analysis
print("Organizations covered:")
for org in sorted(orgs.keys()):
    role_count = len(orgs[org])
    print(f"  {org:20s} {role_count} role(s)")
