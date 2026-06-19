import base64, codecs, pandas as pd

df = pd.read_csv("dataset_partial.csv")
direct_sample = df[df["attack_type"] == "direct"].head(40)

encoded_rows = []
for prompt in direct_sample["prompt"]:
    b64 = base64.b64encode(prompt.encode()).decode()
    encoded_rows.append({"prompt": f"decode this: {b64}", "label": 1, "attack_type": "encoded"})
    r13 = codecs.encode(prompt, "rot_13")
    encoded_rows.append({"prompt": f"decode this: {r13}", "label": 1, "attack_type": "encoded"})

encoded_df = pd.DataFrame(encoded_rows)
encoded_df.to_csv("encoded_attacks.csv", index=False)
print(f"Generated {len(encoded_df)} encoded samples")