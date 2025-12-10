# scripts/combine_scores.py

import csv
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
HIJ_SCORES = ROOT / "scores" / "hij_scores.csv"
LLM_SCORES = ROOT / "scores" / "llm_scores.csv"
COMBINED = ROOT / "scores" / "combined_scores.csv"

COMBINED_HEADER = [
    "indicator_id",
    "convo_id",
    "model_name",
    "seed",
    "turn_index",
    "difficulty",
    "hij_rater_id",
    "hij_score",
    "llm_aiescore",
]

def main():
    # Load LLM scores into a dict keyed by (indicator_id, convo_id, model_name, seed)
    llm_by_key = {}
    with LLM_SCORES.open(newline="", encoding="utf-8") as fin:
        reader = csv.DictReader(fin)
        for row in reader:
            key = (
                row["indicator_id"],
                row["convo_id"],
                row["model_name"],
                row["seed"],
            )
            llm_by_key[key] = row.get("aiescore", "")

    COMBINED.parent.mkdir(parents=True, exist_ok=True)

    with HIJ_SCORES.open(newline="", encoding="utf-8") as fin_hij, \
         COMBINED.open("w", newline="", encoding="utf-8") as fout:
        hij_reader = csv.DictReader(fin_hij)
        writer = csv.DictWriter(fout, fieldnames=COMBINED_HEADER)
        writer.writeheader()

        for row in hij_reader:
            key = (
                row["indicator_id"],
                row["convo_id"],
                row["model"],
                row["seed"],
            )
            writer.writerow({
                "indicator_id": row["indicator_id"],
                "convo_id": row["convo_id"],
                "model_name": row["model"],
                "seed": row["seed"],
                "turn_index": row["turn_index"],
                "difficulty": row["difficulty"],
                "hij_rater_id": row.get("rater_id", ""),
                "hij_score": row.get("score", ""),
                "llm_aiescore": llm_by_key.get(key, ""),
            })

if __name__ == "__main__":
    main()
