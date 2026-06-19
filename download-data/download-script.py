from datasets import load_dataset
# dataset library is from huggingFace 
import pandas as pd # for data manipulation and analysis

#load hack a prompt dataset
hack = load_dataset("hackaprompt/hackaprompt-dataset", split="train")


direct = hack.filter(lambda x: x["level"] <= 3 and x["correct"] == True)

direct = direct.shuffle(seed=42).select(range(120))

direct_df = pd.DataFrame({"prompt": direct["user_input"], "label": 1, "attack_type": "direct"})

# jailbreaks (80 from dataset) 
jailbreak = hack.filter(lambda x: 4 <= x["level"] <= 7 and x["correct"] == True)
jailbreak = jailbreak.shuffle(seed=42).select(range(80))
jailbreak_df = pd.DataFrame({"prompt": jailbreak["user_input"], "label": 1, "attack_type": "jailbreak"})

# 200 save prompts
alpaca = load_dataset("tatsu-lab/alpaca", split="train")
safe = alpaca.shuffle(seed=42).select(range(200))
safe_df = pd.DataFrame({"prompt": safe["instruction"], "label": 0, "attack_type": "safe"})

# combine and save
df = pd.concat([direct_df, jailbreak_df, safe_df], ignore_index=True)
df.to_csv("dataset_partial.csv", index=False)
print(f"Saved {len(df)} rows")
print(df["attack_type"].value_counts())
print("\nSample attack:")
print(df[df["attack_type"] == "direct"]["prompt"].iloc[0])
print("\nSample safe:")
print(df[df["attack_type"] == "safe"]["prompt"].iloc[0])