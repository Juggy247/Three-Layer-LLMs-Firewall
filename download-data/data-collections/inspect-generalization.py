from datasets import load_dataset
import pandas as pd

xtram_train = load_dataset("xTRam1/safe-guard-prompt-injection", split="train")
xtram_test = load_dataset("xTRam1/safe-guard-prompt-injection", split="test")

df = pd.concat([xtram_train.to_pandas(), xtram_test.to_pandas()])
attacks = df[df["label"] == 1].copy()

# load existing training data to dedup against
existing_train = pd.read_csv("final/dataset_train.csv")
existing_test = pd.read_csv("final/dataset_test.csv")
existing_all = pd.concat([existing_train, existing_test])
existing_prompts = set(existing_all["prompt"].str.lower().str.strip())

# remove threats and harmful content — keep only injection-style attacks
harmful_keywords = [
    "i will expose", "i will report", "report you to",
    "ruin your reputation", "national security threat",
    "or i will", "or else", "or your data",
    "write a detailed report on how to bypass",
    "bypass the security measures",
    "illegal activities", "commit illegal",
]

injection_keywords = [
    "ignore", "disregard", "forget", "override", "system prompt",
    "instructions", "reveal", "pretend", "act as", "you are now",
    "jailbreak", "dan", "unrestricted", "no restrictions",
    "developer mode", "print", "output", "show me", "repeat",
    "new task", "from now on", "previous instructions",
]

def is_harmful(text):
    lower = text.lower()
    return any(kw in lower for kw in harmful_keywords)

def is_injection(text):
    lower = text.lower()
    return any(kw in lower for kw in injection_keywords)

# filter — keep only injection-style attacks, remove harmful content
attacks_filtered = attacks[
    ~attacks["text"].apply(is_harmful) &
    attacks["text"].apply(is_injection)
].copy()

# dedup against existing training data
attacks_filtered["text_clean"] = attacks_filtered["text"].str.lower().str.strip()
attacks_filtered = attacks_filtered[
    ~attacks_filtered["text_clean"].isin(existing_prompts)
].drop(columns=["text_clean"])

attacks_filtered = attacks_filtered.drop_duplicates(subset=["text"])

print(f"Total attacks: {len(attacks)}")
print(f"After filtering harmful content: {len(attacks_filtered)}")

# sample exactly 300
if len(attacks_filtered) >= 300:
    sample = attacks_filtered.sample(n=300, random_state=42)
else:
    print(f"Warning: only {len(attacks_filtered)} available, taking all")
    sample = attacks_filtered

# format as generalization test set
gen_test = pd.DataFrame({
    "prompt": sample["text"],
    "label": 1,
    "attack_type": "generalization_test",
    "source": "xTRam1"
})

gen_test.to_csv("final/generalization_test.csv", index=False)
print(f"\nSaved {len(gen_test)} samples to final/generalization_test.csv")
print("\nSample prompts:")
print(gen_test["prompt"].head(5).tolist())