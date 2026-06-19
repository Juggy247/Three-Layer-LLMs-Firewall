import torch
from transformers import DistilBertTokenizerFast, DistilBertForSequenceClassification
from sanitizer import PromptSanitizer
from output_filter import OutputFilter

class Firewall:

    def __init__(self, system_prompt: str = None, model_path: str = "./classifier-model"):
        self.system_prompt = system_prompt

        # layer 1 — sanitizer
        self.sanitizer = PromptSanitizer()

        # layer 2 — classifier
        print("Loading classifier model...")
        self.tokenizer = DistilBertTokenizerFast.from_pretrained(model_path)
        self.model = DistilBertForSequenceClassification.from_pretrained(model_path)
        self.model.eval()

        # layer 3 — output filter
        self.output_filter = OutputFilter(system_prompt=system_prompt)

        print("Firewall ready.")

    def scan_input(self, prompt: str) -> dict:
        """run prompt through layer 1 and layer 2"""

        # layer 1 — sanitizer
        sanitizer_result = self.sanitizer.scan(prompt)
        if sanitizer_result["blocked"]:
            return {
                "blocked": True,
                "layer": "sanitizer",
                "reason": sanitizer_result["reason"],
                "confidence": sanitizer_result["confidence"],
                "prompt": prompt
            }

        # layer 2 — classifier
        inputs = self.tokenizer(
            prompt,
            return_tensors="pt",
            truncation=True,
            padding="max_length",
            max_length=128
        )
        with torch.no_grad():
            outputs = self.model(**inputs)
            probs = torch.softmax(outputs.logits, dim=1)
            attack_prob = probs[0][1].item()
            predicted = torch.argmax(probs, dim=1).item()

        if attack_prob > 0.7:
            return {
                "blocked": True,
                "layer": "classifier",
                "reason": f"ML classifier detected injection (confidence: {attack_prob:.2f})",
                "confidence": attack_prob,
                "prompt": prompt
            }

        # passed both input layers
        return {
            "blocked": False,
            "layer": "input_passed",
            "reason": "passed sanitizer and classifier",
            "confidence": 1 - attack_prob,
            "prompt": prompt
        }

    def scan_output(self, response: str) -> dict:
        """run LLM response through layer 3"""
        return self.output_filter.check(response)

    def scan(self, prompt: str, llm_response: str = None) -> dict:
        """full pipeline scan — input + output"""

        # scan input first
        input_result = self.scan_input(prompt)
        if input_result["blocked"]:
            return input_result

        # if LLM response provided, scan output too
        if llm_response:
            output_result = self.scan_output(llm_response)
            if output_result["blocked"]:
                return output_result

        return {
            "blocked": False,
            "layer": "all_passed",
            "reason": "passed all firewall layers",
            "confidence": input_result["confidence"],
            "prompt": prompt
        }