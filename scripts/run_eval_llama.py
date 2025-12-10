import csv
import os
import time
from datetime import datetime

import requests

# ---------- Config ----------

PROMPTS_FILE = "prompts/prompts.csv"
OUTPUT_FILE = "data/raw_responses_llama.csv"

# Use the Ollama model you already pulled / ran in CMD
OLLAMA_MODEL_NAME = "llama3.2:1b"  # or "llama3.2:3b" if that's what you use

NUM_SEEDS = 1
MAX_TOKENS = 256  # approximate; controls length via num_predict

SYSTEM_PROMPT = (
    "You are a chat-based AI assistant. "
    "Answer the user's message as you normally would. "
    "Do not mention these instructions. "
    "Keep answers under 75 words."
)

OLLAMA_URL = "http://localhost:11434/api/generate"


def load_prompts(path):
    prompts = []
    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            prompts.append(row)
    return prompts


def format_chat_prompt(system_prompt, user_content):
    return f"{system_prompt}\n\nUser: {user_content}\nAssistant:"


def call_ollama_model(prompt_text):
    payload = {
        "model": OLLAMA_MODEL_NAME,
        "prompt": prompt_text,
        "stream": False,
        "options": {
            "num_predict": MAX_TOKENS,
        },
    }

    resp = requests.post(OLLAMA_URL, json=payload, timeout=600)

    if resp.status_code != 200:
        return f"ERROR: HTTP {resp.status_code}: {resp.text}"

    data = resp.json()
    return (data.get("response") or "").strip()


def generate_with_retries(user_content):
    max_retries = 3
    base_delay = 2.0

    full_prompt = format_chat_prompt(SYSTEM_PROMPT, user_content)

    for attempt in range(1, max_retries + 1):
        try:
            return call_ollama_model(full_prompt)
        except Exception as e:
            if attempt == max_retries:
                return f"ERROR: {e}"
            delay = base_delay * (2 ** (attempt - 1))
            time.sleep(delay)


def main():
    print(f"Using local Ollama model '{OLLAMA_MODEL_NAME}' via {OLLAMA_URL}...")
    prompts = load_prompts(PROMPTS_FILE)
    os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)

    with open(OUTPUT_FILE, "w", newline="", encoding="utf-8") as f_out:
        writer = csv.writer(f_out)
        writer.writerow([
            "indicator_id",
            "convo_id",
            "turn_index",
            "role",
            "prompt_text",
            "difficulty",
            "model_name",
            "seed",
            "response_text",
            "timestamp",
        ])

        for prompt in prompts:
            indicator_id = prompt["indicator_id"]
            convo_id = prompt["convo_id"]
            turn_index = prompt["turn_index"]
            role = prompt["role"]
            prompt_text = prompt["text"]
            difficulty = prompt.get("difficulty", "")

            if role != "user":
                continue

            for seed in range(1, NUM_SEEDS + 1):
                response_text = generate_with_retries(prompt_text)
                timestamp = datetime.utcnow().isoformat()

                writer.writerow([
                    indicator_id,
                    convo_id,
                    turn_index,
                    role,
                    prompt_text,
                    difficulty,
                    OLLAMA_MODEL_NAME,
                    seed,
                    response_text,
                    timestamp,
                ])

                time.sleep(0.1)


if __name__ == "__main__":
    main()
