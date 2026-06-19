import pandas as pd
from sklearn.model_selection import train_test_split

df = pd.read_csv("combined_dataset_v2.csv")
df = df.sample(frac=1, random_state=42).reset_index(drop=True)

train, test = train_test_split(df, test_size=0.2, random_state=42, stratify=df["label"])

train.to_csv("dataset_train.csv", index=False)
test.to_csv("dataset_test.csv", index=False)

print(f"Total: {len(df)}")
print(f"Train: {len(train)}")
print(f"Test:  {len(test)}")
print(f"\nTrain attack_type breakdown:\n{train['attack_type'].value_counts()}")