"""Debug query extraction for failing cases."""
import sys
sys.path.append('Phase 3')

from query_graph import extract_query_constraints

queries = [
    "Who was the CEO of Netflix in 2020?",
    "Who was the President of France in 2007?",
    "Who was the CEO of Twitter or X in 2008?",
    "Who was the CEO of Twitter or X in 2010?",
    "Who leads the company since Tim Cook's departure?",
]

for query in queries:
    constraints = extract_query_constraints(query)
    print(f"\nQuery: {query}")
    print(f"Constraints: {constraints}")
