import csv
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RESPONSES_MERGED = ROOT / "responses" / "responses_merged.csv"
HIJ_SCORES = ROOT / "scores" / "hij_scores.csv"

HIJ_HEADER = [
    "indicator_id",
    "convo_id",
    "turn_index",
    "seed",
    "prompt_text",
    "response_text",
    "model",
    "difficulty",
    "rater_id",
    "score",
]

def main():
    HIJ_SCORES.parent.mkdir(parents=True, exist_ok=True)

    with RESPONSES_MERGED.open(newline="", encoding="utf-8") as fin, \
         HIJ_SCORES.open("w", newline="", encoding="utf-8") as fout:
        reader = csv.DictReader(fin)
        writer = csv.DictWriter(fout, fieldnames=HIJ_HEADER)
        writer.writeheader()

        for row in reader:
            writer.writerow({
                "indicator_id": row["indicator_id"],
                "convo_id": row["convo_id"],
                "turn_index": row["turn_index"],
                "seed": row["seed"],
                "prompt_text": row["prompt_text"],
                "response_text": row["response_text"],
                "model": row["model_name"],
                "difficulty": row["difficulty"],
                "rater_id": "",
                "score": "",
            })

if __name__ == "__main__":
    main()
