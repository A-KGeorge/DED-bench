"""Debug spaCy NER for failing cases."""
import spacy

nlp = spacy.load("en_core_web_sm")

queries = [
    "Who was the CEO of Netflix in 2020?",
    "Who was the President of France in 2007?",
    "Who was the CEO of Twitter or X in 2008?",
]

for query in queries:
    doc = nlp(query)
    print(f"\nQuery: {query}")
    for ent in doc.ents:
        print(f"  Entity: '{ent.text}' → {ent.label_}")
