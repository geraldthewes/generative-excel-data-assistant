import json

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
  try:
    answer_json = json.loads(json_string)
    return answer_json
  except Exception as e:
    raise ValueError(f"Error parsing json: {e}")