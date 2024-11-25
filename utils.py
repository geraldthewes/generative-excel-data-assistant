import json
import requests
import os

def answer_to_json(answer: str) -> dict:
  start_json = 0
  end_json = answer[::-1].find("}")
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
  if json_string == "":
    raise ValueError(f"Could not extract llm ansewr: '{answer}'")
  try:
    answer_json = json.loads(json_string)
    return answer_json
  except Exception as e:
    raise ValueError(f"Error parsing json: {e}")
  

def get_currency_exchange_rates_chf_base():
    url = "https://cdn.jsdelivr.net/npm/@fawazahmed0/currency-api@latest/v1/currencies/chf.json"
    response = requests.get(url)
    data = response.json()["chf"]
    return data

def get_currency_conversion_rate(from_currency, to_currency):
    exchange_rates_chf_base = get_currency_exchange_rates_chf_base()
    from_currency = from_currency.lower()
    to_currency = to_currency.lower()
    if from_currency == to_currency:
        return 1
    elif from_currency == "chf":
        return exchange_rates_chf_base[to_currency]
    elif to_currency == "chf":
        return 1 / exchange_rates_chf_base[from_currency]
    else:
        return exchange_rates_chf_base[to_currency] / exchange_rates_chf_base[from_currency]