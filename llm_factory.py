import os
import time
from llmhub_client import LLMHub
from transformers import AutoModelForCausalLM, AutoTokenizer, pipeline
from dotenv import load_dotenv

load_dotenv()


class LlmHubWrapper:
    def __init__(self):
        self.client = LLMHub(api_key=os.getenv("LLMHUB_API_KEY", ""))
        self.model = self.client.get_models()[0]["model"]

    def __call__(self, history: list):
        try:
            completion = self.client.chat.completions.create(
                model=self.model,
                messages=history,
                temperature=0.7,
                stream=True,
            )
            for chunk in completion:
                delta = chunk.choices[0].delta.content
                time.sleep(0.05)
                yield delta
        except Exception as e:
            yield str(e)


class Phi3Wrapper:
    def __init__(self, model_name):
        self.model = AutoModelForCausalLM.from_pretrained(
            model_name,
            device_map="cuda",
            torch_dtype="auto",
            trust_remote_code=True,
        )
        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        self.generation_args = {
            "max_new_tokens": 500,
            "return_full_text": False,
            "temperature": 1.0,
            "do_sample": False,
        }
        self.pipe = pipeline(
            "text-generation",
            model=self.model,
            tokenizer=self.tokenizer,
        )

    def __call__(self, history: list):
        output = self.pipe(history, **self.generation_args)
        return output[0]["generated_text"]


def llm_factory(model_name: str):
    if model_name == "llmhub":
        return LlmHubWrapper()
    elif model_name == "phi3":
        return Phi3Wrapper("microsoft/Phi-3.5-mini-instruct")
    else:
        raise ValueError(f"Model {model_name} not supported")


if __name__ == "__main__":
    llm = llm_factory("llmhub")
