import pandas as pd

BASE = "responses/raw_responses_gemini.csv"
NEW = "responses/raw_responses_llama.csv"
OUT = "responses/responses_merged.csv"

# Load existing and new
base = pd.read_csv(BASE)
new = pd.read_csv(NEW)

# Inspect columns to map them if needed
print("BASE columns:", base.columns.tolist())
print("NEW columns:", new.columns.tolist())


# Ensure all required columns exist in NEW (add empty ones if missing)
for col in base.columns:
    if col not in new.columns:
        new[col] = None

# Restrict NEW to the same column order as BASE
new = new[base.columns]

# Define composite key to prevent duplicates
key_cols = ["indicator_id", "convo_id", "turn_index", "model_name", "seed"]

# If NEW is missing any key columns, that's a schema problem; fail fast
missing_keys = [c for c in key_cols if c not in new.columns]
if missing_keys:
    raise ValueError(f"NEW is missing key columns: {missing_keys}")

# Drop any NEW rows whose key already exists in BASE
base_keys = set(
    tuple(x) for x in base[key_cols].astype(str).itertuples(index=False, name=None)
)
mask = []
for row in new[key_cols].astype(str).itertuples(index=False, name=None):
    mask.append(tuple(row) not in base_keys)
new = new[mask]

print(f"Appending {len(new)} new rows to {len(base)} existing rows.")

merged = pd.concat([base, new], ignore_index=True)
merged.to_csv(OUT, index=False)
