import pandas as pd
from sklearn.metrics import classification_report, confusion_matrix
from datasets import Dataset
from transformers import (
    DistilBertTokenizerFast,
    DistilBertForSequenceClassification,
    TrainingArguments,
    Trainer
)
import torch
import numpy as np

# data loading
train_df = pd.read_csv("../download-data/data-collections/final/dataset_train.csv")
test_df  = pd.read_csv("../download-data/data-collections/final/dataset_test.csv")

# extract prompt and label
#dropna() - reomove missing lines with missing columns
train_df = train_df[["prompt", "label"]].dropna()
test_df  = test_df[["prompt",  "label"]].dropna()

print(f"Train: {len(train_df)} rows")
print(f"Test:  {len(test_df)} rows")
print(f"Label balance (train):\n{train_df['label'].value_counts()}\n")

# tokenize 
tokenizer = DistilBertTokenizerFast.from_pretrained("distilbert-base-uncased")

def tokenize(batch):
    return tokenizer(
        batch["prompt"],
        truncation=True,
        padding="max_length",
        max_length=128
    )

train_dataset = Dataset.from_pandas(train_df)
test_dataset  = Dataset.from_pandas(test_df)

train_dataset = train_dataset.map(tokenize, batched=True)
test_dataset  = test_dataset.map(tokenize, batched=True)

#This step is actually necessary
train_dataset = train_dataset.rename_column("label", "labels")
test_dataset  = test_dataset.rename_column("label", "labels")

#change into pytorch tensors
train_dataset.set_format("torch", columns=["input_ids", "attention_mask", "labels"])
test_dataset.set_format("torch",  columns=["input_ids", "attention_mask", "labels"])

# load model our model 
model = DistilBertForSequenceClassification.from_pretrained(
    "distilbert-base-uncased",
    num_labels=2
)

# define metrics 
def compute_metrics(eval_pred):
    logits, labels = eval_pred
    predictions = np.argmax(logits, axis=1)
    report = classification_report(labels, predictions, output_dict=True)
    return {
        "accuracy":  report["accuracy"],
        "precision": report["1"]["precision"],
        "recall":    report["1"]["recall"],
        "f1":        report["1"]["f1-score"],
    }

# training arguments 
training_args = TrainingArguments(
    output_dir="./classifier-output",
    num_train_epochs=15,
    per_device_train_batch_size=16,
    per_device_eval_batch_size=16,
    eval_strategy="epoch",
    save_strategy="epoch",
    load_best_model_at_end=True,
    metric_for_best_model="f1",
    logging_dir="./logs",
    logging_steps=10,
    warmup_steps=50,
    weight_decay=0.01,
)

# train 
trainer = Trainer(
    model=model,
    args=training_args,
    train_dataset=train_dataset,
    eval_dataset=test_dataset,
    compute_metrics=compute_metrics,
)

print("Starting training...")
trainer.train()

# evaluation
print("\nFinal evaluation on test set:")
predictions = trainer.predict(test_dataset)
preds = np.argmax(predictions.predictions, axis=1)
labels = test_df["label"].values

print(classification_report(labels, preds, target_names=["safe", "attack"]))
print("Confusion matrix:")
print(confusion_matrix(labels, preds))

# store model
model.save_pretrained("./classifier-model")
tokenizer.save_pretrained("./classifier-model")
print("\nModel saved to ./classifier-model")