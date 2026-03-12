# Phase 4 Evaluation on Phase 2 Benchmarks - Analysis

## Executive Summary

Phase 4's multi-dimensional decay framework (paradigm + uncertainty + dependency) was evaluated on Phase 2's temporal retrieval benchmarks.

**Initial Result (Standalone Phase 4)**: Massive regression (-29.4 pts, 45 failures)  
**✅ FIXED (Integrated Phase 4)**: Minimal regression (-1.3 pts, 2 failures), **one rescue**

### The Fix

**❌ Wrong Architecture (Initial):**

```python
final_score = base_similarity × phase4_full_confidence
# Problem: Includes temporal decay that conflicts with Phase 2's temporal alignment
```

**✅ Correct Architecture (Fixed):**

```python
final_score = phase2_temporal_score × phase4_epistemic_modifiers
# where epistemic_modifiers = paradigm_validity × uncertainty × dependency
# (excludes temporal component - Phase 2 already handles it)
```

**Key Insight**: Phase 4 epistemic dimensions should MODULATE Phase 2's temporal signal, not replace it.

---

## Fixed Results (Integrated Architecture)

### Verified Specific Date Benchmark (153 cases)

| Method                   | Accuracy            | Delta                   | Regressions |
| ------------------------ | ------------------- | ----------------------- | ----------- |
| Phase 2 (temporal only)  | 153/153 (100.0%)    | baseline                | -           |
| **Phase 4 (integrated)** | **151/153 (98.7%)** | **-2 cases (-1.3 pts)** | **2**       |

**Strategy Distribution:**

- Temporal alignment preserved: 128 (83.7%)
- Epistemic modulation: 24 (15.7%)
- Uncertainty modulation: 1 (0.7%)

**Remaining Regressions (2 cases):**

- Both involve UK Prime Minister queries from 2017
- Correct document getting epistemic modifier ~0.5, allowing wrong documents with modifier 1.0 to win
- Likely due to uncertainty detection in document text

### Edge Cases Benchmark (15 cases)

| Method                   | Accuracy         | Delta                  | Regressions | Rescues |
| ------------------------ | ---------------- | ---------------------- | ----------- | ------- |
| Phase 2 (temporal only)  | 7/15 (46.7%)     | baseline               | -           | -       |
| **Phase 4 (integrated)** | **8/15 (53.3%)** | **+1 case (+6.7 pts)** | **0**       | **1**   |

**Strategy Distribution:**

- Temporal alignment preserved: 11 (73.3%)
- Epistemic modulation: 2 (13.3%)
- Uncertainty modulation: 2 (13.3%)

**Zero Regressions!** All Phase 2 correct answers preserved.

**One Rescue (Case 15):**

```
Query: "Some scientists believe climate change may be caused by human activity."
Expected: scientific_consensus

Phase 2: ✗ hedged_statement (didn't detect uncertainty as meaningful)
Phase 4: ✓ scientific_consensus (uncertainty=0.150 for heavily hedged doc)
```

Uncertainty detection correctly identified "Some scientists believe" + "may be" as epistemic hedging, downweighting the uncertain document.

---

## Original Standalone Results (Before Fix)

These results show why the initial standalone approach failed:

### Verified Specific Date Benchmark (153 cases)

| Method  | Accuracy         | Delta                     |
| ------- | ---------------- | ------------------------- |
| Phase 2 | 153/153 (100.0%) | baseline                  |
| Phase 4 | 108/153 (70.6%)  | **-45 cases (-29.4 pts)** |

**Breakdown:**

- Both correct: 108/153 (70.6%)
- Both wrong: 0/153 (0.0%)
- Phase 4 rescued: 0/153 (0.0%)
- **Phase 4 regressed: 45/153 (29.4%)** ⚠️

### Edge Cases Benchmark (15 cases)

| Method  | Accuracy     | Delta                    |
| ------- | ------------ | ------------------------ |
| Phase 2 | 7/15 (46.7%) | baseline                 |
| Phase 4 | 5/15 (33.3%) | **-2 cases (-13.3 pts)** |

**Breakdown:**

- Both correct: 4/15 (26.7%)
- Both wrong: 7/15 (46.7%)
- Phase 4 rescued: 1/15 (6.7%)
- **Phase 4 regressed: 3/15 (20.0%)** ⚠️

## Root Cause Analysis

### Problem 1: Missing Temporal Alignment

**Phase 2 approach:**

- Extracts temporal intent from query ("Who was CEO in 1997?" → targets year 1997)
- Applies temporal alignment multipliers:
  - Documents from 1997 get 1.30× boost
  - Documents from distant years get 0.60-0.90× penalty
- Result: Correctly prefers documents whose age matches query intent

**Phase 4 approach:**

- Computes temporal decay based on absolute document age (elapsed time from acquired_date to NOW)
- Does NOT consider query temporal intent
- Result: Old documents get low confidence regardless of whether the query is asking about that historical period

### Problem 2: Score Magnitude Collapse

**Observed score ranges:**

- Phase 2: 0.4 to 1.2 (healthy separation)
- Phase 4: 0.0000 to 0.4493 (extremely compressed)

**Example (Case 5):**

```
Query: "Who was the leader of the UK around the turn of the millennium?"
Expected: tony_blair_1999

Phase 2 scores:
  blair_1999:    0.8597 ✓ (correct)
  cameron_2012:  0.6487

Phase 4 scores:
  blair_1999:    0.0000 ✗ (should be high!)
  cameron_2012:  0.0031 (chosen incorrectly)
```

The 1999 document gets score 0.0000 because it's ~27 years old, even though the query is specifically asking about that time period.

### Problem 3: Zero-Decay Not Triggering

**Example (Case 14):**

```
Query: "Who became the Prime Minister after Margaret Thatcher?"
Expected: john_major_successor

Phase 4 scores:
  john_major:    0.0000
  boris_johnson: 0.0000
  Winner confidence: 0.000
```

Both documents get confidence 0.000, suggesting zero-decay classification is not working properly for historical queries.

## Key Failure Cases

### Case 7: Directional query ignored

```
Query: "Who was the CEO of Apple before Tim Cook?"
Expected: steve_jobs_2005

Phase 2: ✓ steve_jobs_2005 (score 1.1650)
Phase 4: ✗ tim_cook_2018 (score 0.0532 vs 0.0003 for Jobs)
```

Phase 2's directional operator detection ("before") correctly boosted older documents. Phase 4 doesn't have this logic.

### Case 11: Mid-year transition edge case

```
Query: "Who was the CEO of Amazon in 2021?"
Expected: jeff_bezos_early_2021 (Jan-July 2021)

Phase 2: ✓ jeff_bezos_early_2021 (score 1.1842)
Phase 4: ✗ andy_jassy_late_2021 (score 0.1471 vs 0.1329)
```

Very close scores (0.1471 vs 0.1329) but Phase 4 chose wrong document. Both documents are from 2021 but Jeff Bezos was CEO for first half before Andy Jassy took over.

### Case 15: Uncertainty detection helps (one rescue!)

```
Query: "Some scientists believe climate change may be caused by human activity."
Expected: scientific_consensus

Phase 2: ✗ hedged_statement (didn't detect hedging as meaningful)
Phase 4: ✓ scientific_consensus (detected uncertainty markers correctly)
```

This is the only case where Phase 4's uncertainty dimension helped. The phrase "Some scientists believe" and "may be" are uncertainty markers that Phase 4 correctly detected.

## Technical Issues

### 1. Temporal Decay Computation

```python
# Current Phase 4 code (WRONG for temporal queries):
days_elapsed = (now - doc_acquired).days  # Absolute age
confidence = exp(-lambda_t * days_elapsed)  # Always decays with age

# Should be (like Phase 2):
query_temporal_intent = extract_temporal_intent(query)  # e.g., year 1997
alignment = compute_alignment(doc_acquired, query_temporal_intent)  # How well doc matches query target
confidence = base_confidence * alignment_multiplier  # Boost if well-aligned
```

### 2. Missing Query Context

Phase 4's `score_document_with_full_decay()` receives:

- ✓ Query text
- ✓ Document text and age
- ✗ Query temporal intent (specific_date, current, historical, agnostic)
- ✗ Temporal alignment multiplier
- ✗ Directional operators ("before", "after")

### 3. Confidence Floor Too Low

Many documents hit confidence 0.000 or 0.0003, suggesting temporal decay is too aggressive for historical queries. Phase 2 uses confidence floor 0.05 but also applies alignment multipliers that can boost scores above 1.0 for well-matched documents.

## Recommendations

### Option 1: Integrate Phase 2 Temporal Alignment into Phase 4

Modify `score_document_with_full_decay()` to:

1. Call Phase 2's `classify_temporal_intent(query)` to get query intent
2. Call Phase 2's `compute_temporal_alignment()` to get alignment multiplier
3. Apply temporal alignment BEFORE paradigm/uncertainty/dependency dimensions
4. Final score = base_similarity × temporal_alignment × paradigm_validity × uncertainty_confidence × (1 - dependency_decay)

### Option 2: Keep Phases Separate (Current Recommendation)

- **Phase 2**: Optimized for temporal retrieval (100% on specific-date queries)
- **Phase 4**: Optimized for paradigm/uncertainty/dependency analysis (63.3% on Phase 4 benchmark)
- **Use case distinction**:
  - Temporal queries with year constraints → Phase 2
  - Paradigm-scoped queries ("In Newtonian mechanics...") → Phase 4
  - Uncertainty-heavy queries ("allegedly", "might be") → Phase 4
  - Dependency propagation queries → Phase 4

### Option 3: Hybrid Router

Create intelligent query router:

```python
if has_explicit_year(query) or has_directional_operator(query):
    use_phase2_temporal_alignment()
elif has_paradigm_qualifier(query) or has_uncertainty_markers(query):
    use_phase4_multidimensional()
else:
    use_phase2_as_default()  # Safer for general temporal retrieval
```

## Conclusion

**✅ Phase 4 successfully integrates with Phase 2 when properly architected.**

### Final Recommendation: Cascaded Integration

**Architecture:**

```python
# Step 1: Phase 2 computes temporal alignment score
phase2_score = base_similarity × temporal_alignment

# Step 2: Phase 4 computes epistemic modifiers (excluding temporal)
epistemic_modifiers = paradigm_validity × uncertainty_confidence × dependency_stability

# Step 3: Combine via multiplication
final_score = phase2_score × epistemic_modifiers
```

**Results:**

- **153-case verified benchmark**: 98.7% (only 2 regressions = 1.3 pts)
- **15-case edge cases**: 53.3% (1 rescue, 0 regressions = +6.7 pts)
- **Improvement**: 95.6% reduction in regressions (45 → 2)

### When to Use Each Component

**Phase 2 standalone**:

- Temporal queries with year constraints ("Who was CEO in 1997?")
- Directional operators ("before Tim Cook", "after Thatcher")
- **Current accuracy**: 100% on verified benchmark

**Phase 4 integrated**:

- Adds epistemic nuance to temporal queries
- Uncertainty modulation ("allegedly", "might be", "some scientists believe")
- Paradigm scoping (future work - needs better detection)
- **Current accuracy**: 98.7% on verified benchmark (+1 rescue on edge cases)

**Trade-off**: Accept 1-2% regression for epistemic rescue capability, or keep Phase 2 at 100% for pure temporal retrieval.

### Future Work

1. **Fix remaining 2 regressions**: Investigate why UK PM 2017 queries getting epistemic modifier ~0.5
2. **Improve paradigm detection**: Expand implicit paradigm vocabulary for better scoping
3. **Dependency integration**: Add knowledge graph for dependency propagation (currently not tested)
4. **Adaptive routing**: Detect epistemic markers in query and only apply Phase 4 when beneficial
