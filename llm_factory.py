import os
import time
from llmhub_client import LLMHub
from transformers import AutoModelForCausalLM, AutoTokenizer, pipeline
from dotenv import load_dotenv
import ollama
from openai import AzureOpenAI

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
    def __init__(self, model_name: str):
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

class OllamaWrapper:
    def __init__(self, model_name: str):
        self.model = model_name
        self.client = ollama.Client()

    def __call__(self, history: list):
        try:
            response = self.client.chat(model=self.model, messages=history)
            return response['message']['content']
        except Exception as e:
            raise ValueError(f"Ollama error: {str(e)}")

class OpenAIWrapper:
    def __init__(self, model_name: str = "gpt-4o-mini"):
        self.model = model_name
        client = AzureOpenAI(
            azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT", ""),
            api_key=os.getenv("AZURE_OPENAI_API_KEY"),
            api_version="2024-02-01",
        )

    def __call__(self, history: list):
        try:
            print("MMMMMMMMMMMMMMMODEL")
            response = openai.ChatCompletion.create(
                model=self.model,
                messages=history,
                temperature=0.7,
            )
            return response.choices[0].message.content
        except Exception as e:
            raise ValueError(f"OpenAI error: {str(e)}")


def llm_factory(model_name: str):
    if model_name == "llmhub":
        return LlmHubWrapper()
    elif model_name == "phi3":
        return Phi3Wrapper("microsoft/Phi-3.5-mini-instruct")
    elif model_name == "llama3.2":
        return OllamaWrapper("llama3.2")
    elif model_name == "gpt-4o-mini":
        return OpenAIWrapper("gpt-4o-mini")
    else:
        raise ValueError(f"Model {model_name} not supported")

if __name__ == "__main__":
    llm = llm_factory(os.getenv("MODEL_NAME", ""))
    print(f"Model in use: {os.getenv('MODEL_NAME', '')}")
