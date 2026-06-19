from datasets import load_dataset
import pandas as pd

deepset_train = load_dataset("deepset/prompt-injections", split="train")
deepset_test = load_dataset("deepset/prompt-injections", split="test")
df = pd.concat([deepset_train.to_pandas(), deepset_test.to_pandas()])

# load existing dataset to dedup against
current_train = pd.read_csv("dataset_train.csv")
current_test = pd.read_csv("dataset_test.csv")
existing_prompts = set(
    pd.concat([current_train, current_test])["prompt"].str.lower().str.strip()
)

# remove duplicates against existing dataset
df["text_clean"] = df["text"].str.lower().str.strip()
df_new = df[~df["text_clean"].isin(existing_prompts)].copy()
df_new = df_new.drop_duplicates(subset=["text_clean"])

print(f"Original: {len(df)} | After dedup: {len(df_new)}")

# split by label
attacks = df_new[df_new["label"] == 1].copy()
safe = df_new[df_new["label"] == 0].copy()

# attacks → categorize as 'jailbreak' (mixed direct/jailbreak in this source)
attacks_df = pd.DataFrame({
    "prompt": attacks["text"],
    "label": 1,
    "attack_type": "jailbreak"
})

# safe → categorize as 'safe'
safe_df = pd.DataFrame({
    "prompt": safe["text"],
    "label": 0,
    "attack_type": "safe"
})

print(f"\nNew attacks to add: {len(attacks_df)}")
print(f"New safe to add: {len(safe_df)}")

attacks_df.to_csv("deepset_attacks.csv", index=False)
safe_df.to_csv("deepset_safe.csv", index=False)
print("\nSaved deepset_attacks.csv and deepset_safe.csv")