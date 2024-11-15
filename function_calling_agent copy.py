import json
from llm_factory import llm_factory
from functions import (
    add_todo_item,
    get_next_departure_time,
    list_todo_items,
    caesar_cipher,
)

tool_descriptions = [
    {
        "function": {
            "name": "get_next_departure_time",
            "description": "Get the next departure time for a train connection",
            "parameters": [
                {
                    "name": "from_station",
                    "type": "string",
                    "description": "The station or city where the train journey starts.",
                },
                {
                    "name": "to_station",
                    "type": "string",
                    "description": "The station or city where the train journey ends.",
                },
            ],
        },
    },
    {
        "function": {
            "name": "add_todo_item",
            "description": "Add a to-do item to the list",
            "parameters": [
                {
                    "name": "item",
                    "type": "string",
                    "description": "The to-do item to add to the list.",
                },
            ],
        },
    },
    {
        "function": {
            "name": "list_todo_items",
            "description": "List all to-do items",
        },
    },
    {
        "function": {
            "name": "llm",
            "description": "Generate text using a language model. Use this function if no other function is suitable.",
            # no parameters as the conversation is stored in the messages variable
        },
    },
    {
        "function": {
            "name": "caesar_cipher",
            "description": "Encrypt and decrypt a text using Caesar Cipher which shifts letters by a given number of positions.",
            "parameters": [
                {
                    "name": "text",
                    "type": "string",
                    "description": "The text to be encrypted or decrypted using Caesar Cipher.",
                },
                {
                    "name": "shift",
                    "type": "string",
                    "description": "The positive (forward, encryption) or negative (backward, decryption) shift in position in the alphabet of each character in the text (default is 3).",
                },
            ],
        },
    },
]

tools_map = {
    "get_next_departure_time": get_next_departure_time,
    "add_todo_item": add_todo_item,
    "list_todo_items": list_todo_items,
    "caesar_cipher": caesar_cipher,
}

function_calling_prompt = """As an AI assistant, please select the most suitable function and parameters from the list of available functions below, based on the user's input.

----------------------------------------

Input: {input}

----------------------------------------

Available functions:
{tools}
----------------------------------------
The output should be in the following format:
"""

prompt_end = """```
{
    "function": "function_name",
    "parameters": {
        "parameter1": "value1",
        "parameter2": "value2",
        ...
    }
}
```

Remember to only give the json object as output, without any additional text."""

class FunctionAgent:
    def __init__(self, model):
        self.model = model
    
    def __call__(self, messages: list[dict[str, str]]):
        try:
            input_text = messages[-1]["content"]
            prompt = (
                function_calling_prompt.format(
                    input=input_text, tools=tool_descriptions
                )
                + prompt_end
            )
            answer = ""
            for x in self.model([{"role": "user", "content": prompt}]):
                answer += x
            start_json = 0
            end_json = answer[::-1].find("}")
            print(f'answer from llm: {answer}')
            braces_stack = []
            for i, c in enumerate(answer):
                if c == "{":
                    braces_stack.append(i)
                elif c == "}":
                    start_json = braces_stack.pop()
                    if not braces_stack:
                        end_json = i
                        break
            json_string = answer[start_json:end_json + 1]
            print(f'extracted json_string from llm answer: {json_string}')
            answer_json = json.loads(json_string)
            function_name = answer_json["function"]
            if function_name == "llm":
                for x in self.model(messages):
                    yield x
            else:
                parameters = answer_json["parameters"]
                yield tools_map[function_name](**parameters)
        except Exception as e:
            yield str(e) + str(answer)

if __name__ == "__main__":
    llm = llm_factory("llmhub")
    llm = FunctionAgent(llm)
    res = ""
    for x in llm([{"role": "user", "content": "Hello, how are you?"}]):
        res += x
    print(res)