from llm_factory import llm_factory
from functions import (
    get_suppliers_by_material,
    compare_price_per_unit_by_quarters,
    excel_test,
    get_material_sales,
)
from utils import answer_to_json

tool_descriptions = [
    {
        "function": {
            "name": "llm",
            "description": "Generate text using a language model. Use this function if no other function is suitable.",
            # no parameters as the conversation is stored in the messages variable
        },
    },
    {
        "function": {
            "name": "get_suppliers_by_material",
            "description": "Get suppliers that deliver a material.",
            "parameters": [
                {
                    "name": "material",
                    "type": "string",
                    "description": "The material to search for.",
                },
            ],
        },
    },
    {
        "function": {
            "name": "compare_price_per_unit_by_quarters",
            "description": "Compare price per unit for two sales quarters. Takes in two sales quarters along with years and returns the average price per unit for the two quarters.",
            "parameters": [
                {
                    "name": "unit_type",
                    "type": "string",
                    "description": "The type of unit to compare.",
                },
                {
                    "name": "quarter1",
                    "type": "string",
                    "description": "The first quarter to compare. Possible values: Q1, Q2, Q3, Q4.",
                },
                {
                    "name": "year1",
                    "type": "int",
                    "description": "The year of the first quarter.",
                },
                {
                    "name": "quarter2",
                    "type": "string",
                    "description": "The second quarter to compare. Possible values: Q1, Q2, Q3, Q4.",
                },
                {
                    "name": "year2",
                    "type": "int",
                    "description": "The year of the second quarter.",
                },
            ],
        },
    },
    {
        "function": {
            "name": "excel_test",
            "description": "Create a test excel file.",
            "parameters": [],
        },
    },
    {
        "function": {
            "name": "get_material_sales",
            "description": "Get the sales of a material of all countries.",
            "parameters": [
                {
                    "name": "material",
                    "type": "string",
                    "description": "The material to search for.",
                },
                {
                    "name": "year",
                    "type": "int",
                    "description": "The year of sales.",
                },
                {
                    "name": "month",
                    "type": "string",
                    "description": "The month of sales. Available values: January, February, March, April, May, June, July, August, September, October, November, December.",
                },
            ],
        },
    },
]

tools_map = {
    "get_suppliers_by_material": get_suppliers_by_material,
    "compare_price_per_unit_by_quarters": compare_price_per_unit_by_quarters,
    "excel_test": excel_test,
    "get_material_sales": get_material_sales
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
            answer_json = answer_to_json(answer)
            function_name = answer_json["function"]
            if function_name == "llm":
                for x in self.model(messages):
                    yield x
            else:
                parameters = answer_json["parameters"]
                yield tools_map[function_name](self.model, **parameters)
        except Exception as e:
            yield str(e) + str(answer)

if __name__ == "__main__":
    llm = llm_factory("llmhub")
    llm = FunctionAgent(llm)
    res = ""
    for x in llm([{"role": "user", "content": "Hello, how are you?"}]):
        res += x
    print(res)