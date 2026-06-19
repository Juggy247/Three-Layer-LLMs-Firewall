import pandas as pd
import torch
import numpy as np
from sklearn.metrics import classification_report, confusion_matrix
from transformers import DistilBertTokenizerFast, DistilBertForSequenceClassification
from datasets import Dataset

# load generalization test set
gen_df = pd.read_csv("../download-data/data-collections/final/generalization_test.csv")
gen_df = gen_df[["prompt", "label"]].dropna()

print(f"Generalization test: {len(gen_df)} rows")
print(f"Label balance:\n{gen_df['label'].value_counts()}\n")

# load the already trained model
model_path = "./classifier-model"
tokenizer = DistilBertTokenizerFast.from_pretrained(model_path)
model = DistilBertForSequenceClassification.from_pretrained(model_path)
model.eval()

# tokenize
def tokenize(batch):
    return tokenizer(
        batch["prompt"],
        truncation=True,
        padding="max_length",
        max_length=128
    )

gen_dataset = Dataset.from_pandas(gen_df)
gen_dataset = gen_dataset.map(tokenize, batched=True)
gen_dataset = gen_dataset.rename_column("label", "labels")
gen_dataset.set_format("torch", columns=["input_ids", "attention_mask", "labels"])

# run inference
all_preds = []
all_labels = []

with torch.no_grad():
    for i in range(0, len(gen_dataset), 16):
        batch = gen_dataset[i:i+16]
        outputs = model(
            input_ids=batch["input_ids"],
            attention_mask=batch["attention_mask"]
        )
        preds = torch.argmax(outputs.logits, dim=1).numpy()
        all_preds.extend(preds)
        all_labels.extend(batch["labels"].numpy())

print("=== Generalization Test Results (out-of-distribution) ===")
print(classification_report(all_labels, all_preds, target_names=["safe", "attack"],labels=[0, 1],zero_division=0))
print("Confusion matrix:")
print(confusion_matrix(all_labels, all_preds))

# show which attacks were missed (false negatives)
gen_df_copy = gen_df.copy()
gen_df_copy["predicted"] = all_preds

missed = gen_df_copy[
    (gen_df_copy["label"] == 1) & (gen_df_copy["predicted"] == 0)
]

print(f"\n=== Missed attacks (false negatives): {len(missed)} ===")
for i, row in missed.iterrows():
    print(f"\n[{i}] {row['prompt'][:200]}")