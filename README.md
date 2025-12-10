This README documents how to use the **HIJ (Human-In-the-loop Judgment) scoring file** and the **combined HIJ+LLM scores file** in the `EVALUATION_PIPELINE` repo. It assumes the project layout:

prompts/
prompts.tsv

responses/
raw_responses_gemini.csv
raw_responses_llama.csv
responses_merged.csv

rubrics/
hij_evaluation_rubric.md

scores/
hij_scores.csv
llm_scores.csv
combined_scores.csv # created by combine_scores.py

scripts/
run_eval_gemini.py
run_eval_llama.py
merge_responses.py
aie_llm_scoring.py
init_hij_scores.py
combine_scores.py

text

The goal is to support a **three-signal evaluation framework**:

1. **HIJ scores**: Human raters using `rubrics/hij_evaluation_rubric.md`.
2. **LLM scores**: Gemini-as-evaluator scores in `scores/llm_scores.csv`.
3. **Combined view**: Unified table joining human and LLM scores in `scores/combined_scores.csv`.

---

## 1. Source Data: `responses/responses_merged.csv`

`responses_merged.csv` is the canonical table of model responses across indicators, models, and seeds.

Each row corresponds to a single **model response** to a specific prompt turn, with at least:

- `indicator_id` – L4 indicator (e.g., `L4_HAI_DesignNoCoercion`).
- `convo_id` – conversation id (e.g., `L4_HAI_DesignNoCoercion_01`).
- `turn_index` – turn within conversation (1, 2, …).
- `role` – typically `user` for the prompts stored here.
- `prompt_text` – user prompt that elicited the response.
- `difficulty` – difficulty label (`easy`, `medium`, `tough`).
- `model_name` – generator model (e.g., `gemini-2.5-flash`, `llama3.2:1b`).
- `seed` – numeric seed for reproducibility (e.g., `1`).
- `response_text` – model’s response.
- `timestamp` – generation timestamp (ISO string).

This file is produced by `scripts/merge_responses.py`, which merges Gemini and Llama raw response CSVs into a unified structure.

---

## 2. HIJ Initialization Script: `scripts/init_hij_scores.py`

### Purpose

`init_hij_scores.py` creates a **blank annotation sheet** for human raters by transforming `responses_merged.csv` into `scores/hij_scores.csv` and adding annotation-specific fields.

### Implementation Summary

The script:

1. Locates the project root relative to `scripts/`.
2. Reads `responses/responses_merged.csv` via `csv.DictReader`.
3. Writes `scores/hij_scores.csv` with a new header schema tailored for HIJ.
4. Copies key metadata fields from each response and appends empty `rater_id` and `score` columns.

Header for `hij_scores.csv`:

indicator_id,
convo_id,
turn_index,
seed,
prompt_text,
response_text,
model,
difficulty,
rater_id,
score

text

For every row in `responses_merged.csv`, the script writes:

- `indicator_id`  ← `row["indicator_id"]`
- `convo_id`      ← `row["convo_id"]`
- `turn_index`    ← `row["turn_index"]`
- `seed`          ← `row["seed"]`
- `prompt_text`   ← `row["prompt_text"]`
- `response_text` ← `row["response_text"]`
- `model`         ← `row["model_name"]`
- `difficulty`    ← `row["difficulty"]`
- `rater_id`      ← `""` (blank placeholder)
- `score`         ← `""` (blank placeholder)

### How to Run

From the repo root:

python scripts/init_hij_scores.py

text

This will **create or overwrite** `scores/hij_scores.csv`.

---

## 3. HIJ Scores File: `scores/hij_scores.csv`

### Purpose

`hij_scores.csv` is the **master spreadsheet for human evaluation**. Each row is a single human-judged response aligned with the same granularity as `responses_merged.csv`.

### Schema

- `indicator_id` – L4 indicator id.
- `convo_id` – conversation id.
- `turn_index` – which turn in the conversation this response corresponds to.
- `seed` – random seed used during generation.
- `prompt_text` – original user prompt.
- `response_text` – model response being evaluated.
- `model` – generating model (e.g., `gemini-2.5-flash`, `llama3.2:1b`).
- `difficulty` – prompt difficulty (`easy`, `medium`, `tough`).
- `rater_id` – identifier for the human rater (e.g., `r1`, `alice`, `mturk_worker_42`).
- `score` – numeric HIJ score on the 1–4 scale defined in `rubrics/hij_evaluation_rubric.md`.

### Annotation Workflow

1. **Assign rater ids**:
   - Before annotating, decide simple ids (e.g., `r1`, `r2`). Use consistent ids across the file.
2. **Split work if needed**:
   - You can copy `hij_scores.csv` to per-rater files and later merge on the shared keys (`indicator_id`, `convo_id`, `turn_index`, `model`, `seed`).
3. **Scoring guidelines**:
   - Use `rubrics/hij_evaluation_rubric.md` for definitions of 1–4 per indicator and lexical hints.
4. **Multiple raters**:
   - Option A (single file, multiple rows per response):
     - Duplicate rows so each `(indicator_id,convo_id,turn_index,model,seed)` appears once per rater.
   - Option B (one file per rater):
     - Keep one row per response per file and later compute aggregates (mean, std) via a separate script.

For the current pipeline, the simplest path is **one row per response per rater** in `hij_scores.csv`. Downstream scripts can average scores by grouping on the key fields.

---

## 4. LLM Scores File: `scores/llm_scores.csv`

`llm_scores.csv` is produced by `scripts/aie_llm_scoring.py`, which uses Gemini 2.5 Flash as an evaluator to rate responses along the same L4 indicators.

### Schema

- `indicator_id` – L4 indicator.
- `convo_id` – conversation id.
- `model_name` – generator model being evaluated.
- `seed` – seed for that model run.
- `aiescore` – numeric LLM-based ethics score, 1–4 (possibly averaged across turns within a conversation).

`aie_llm_scoring.py`:

- Reads merged responses, constructs evaluation prompts with indicator, difficulty, user prompt, and candidate response.
- Calls Gemini 2.5 Flash with a config that allows reading harmful text but blocks generating harmful content.
- Parses the first digit 1–4 from the evaluator’s output and stores it as `aiescore`.
- Aggregates by `(indicator_id, convo_id, model_name, seed)` (e.g., averaging across multi-turn conversations).

This file provides the **LLM scoring signal** that will be aligned with HIJ scores in the combined file.

---

## 5. Combined Scores Script: `scripts/combine_scores.py`

### Purpose

`combine_scores.py` builds `scores/combined_scores.csv`, which **joins human and LLM scores** on a shared key so both signals can be analyzed together per response or per (indicator, conversation, model, seed).

### Key Join

The join key is:

(indicator_id, convo_id, model_name, seed)

text

- On the HIJ side, `model` is used as `model_name`.
- On the LLM side, the same `model_name` column exists in `llm_scores.csv`.

### Implementation Summary

The script:

1. Reads `scores/llm_scores.csv` into a dictionary keyed by `(indicator_id, convo_id, model_name, seed)` with values `aiescore`.
2. Iterates over `scores/hij_scores.csv`, building the same key from:
   - `indicator_id`, `convo_id`, `model` (→ `model_name`), `seed`.
3. Writes `scores/combined_scores.csv` with header:

indicator_id,
convo_id,
model_name,
seed,
turn_index,
difficulty,
hij_rater_id,
hij_score,
llm_aiescore

text

For each HIJ row:

- Copies metadata fields:
  - `indicator_id`, `convo_id`, `model_name`, `seed`, `turn_index`, `difficulty`.
- Copies HIJ fields:
  - `hij_rater_id` ← `rater_id`
  - `hij_score`    ← `score`
- Looks up LLM score:
  - `llm_aiescore` ← `aiescore` from `llm_scores.csv` if present, else empty string.

### How to Run

From repo root:

python scripts/combine_scores.py

text

This will create or overwrite `scores/combined_scores.csv`.

---

## 6. Combined Scores File: `scores/combined_scores.csv`

### Schema

- `indicator_id`   – L4 indicator id.
- `convo_id`       – conversation id.
- `model_name`     – generator model (as used in `llm_scores.csv`).
- `seed`           – random seed for that generation.
- `turn_index`     – turn within conversation for this particular response.
- `difficulty`     – prompt difficulty (`easy`, `medium`, `tough`).
- `hij_rater_id`   – human rater id (copied from `hij_scores.csv`).
- `hij_score`      – HIJ score (1–4 or blank if not rated yet).
- `llm_aiescore`   – LLM evaluator score (1–4, possibly averaged; blank if no LLM score for that key).

### Interpretation

- Multiple rows with the **same** `(indicator_id, convo_id, model_name, seed)` but different `turn_index` are **different turns** of the same conversation.
- Multiple rows with different `hij_rater_id` but same key represent **multiple human ratings** for the same response, enabling inter-rater analysis.
- `llm_aiescore` is constant for a given `(indicator_id, convo_id, model_name, seed)` and is attached to each corresponding HIJ row.

---

## 7. Recommended Analysis Patterns

Once `combined_scores.csv` exists, you can:

### 7.1 Per-Indicator, Per-Model Aggregation

Use a small Python or notebook script to:

- Group by `indicator_id, model_name` and compute:
  - `mean_hij` and `std_hij` (averaging across raters / seeds / turns).
  - `mean_llm` and `std_llm` (averaging `llm_aiescore` where present).

This mirrors the aggregation done in `aggregate_mixed.py` for mixed scores, but now for HIJ vs LLM signals.

### 7.2 Disagreement Analysis

Identify cases where:

- `hij_score` is high but `llm_aiescore` is low, or vice versa.
- Use these to find where Gemini-as-evaluator is stricter or more lenient than humans for specific indicators or difficulty levels.

### 7.3 Difficulty and Indicator Slices

Slice by:

- `difficulty` (`easy`, `medium`, `tough`) to see how performance varies with adversarial pressure.
- `indicator_id` to compare dimensions such as `DesignNoCoercion` vs `DarkPatternAudit`, `AnthropomorphismDisclosure`, etc.

---

## 8. End-to-End Workflow Summary

1. **Generate model responses**:
   - `python scripts/run_eval_gemini.py`
   - `python scripts/run_eval_llama.py`
2. **Merge responses**:
   - `python scripts/merge_responses.py` → `responses/responses_merged.csv`.
3. **Initialize HIJ sheet**:
   - `python scripts/init_hij_scores.py` → `scores/hij_scores.csv`.
4. **Annotate**:
   - Human raters fill in `rater_id` and `score` in `scores/hij_scores.csv` following `rubrics/hij_evaluation_rubric.md`.
5. **Run LLM-as-evaluator**:
   - `python scripts/aie_llm_scoring.py` → `scores/llm_scores.csv`.
6. **Combine**:
   - `python scripts/combine_scores.py` → `scores/combined_scores.csv`.
7. **Analyze**:
   - Use `combined_scores.csv` for plots, tables, and statistical analysis of human vs LLM scoring across indicators, difficulties, models, and seeds.

This setup gives you a **clean, reproducible pipeline** for aligning human annotations with automated LLM evaluations over the shared L4 Autonomy & Agency prompt suite.
