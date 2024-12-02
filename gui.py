import gradio as gr
import pandas as pd
import os
import shutil
from function_calling_agent import FunctionAgent
from llm_factory import llm_factory
from typing import List, Dict, Any
from datetime import datetime
from dotenv import load_dotenv
import json

load_dotenv()

llm = llm_factory(os.getenv("MODEL_NAME", ""))
calling_agent = FunctionAgent(llm)

# Define the tmp folder
tmp_folder = os.path.join(os.getcwd(), "tmp")

# Ensure tmp folder exists
if not os.path.exists(tmp_folder):
    os.makedirs(tmp_folder)

# Function to clean up the tmp folder after program ends
def cleanup():
    json_path = os.path.join(tmp_folder, "file_mapping.json")
    if os.path.exists(json_path):
        os.remove(json_path)
    if os.path.exists(tmp_folder):
        shutil.rmtree(tmp_folder)
    os.mkdir(tmp_folder)

def handle_file_upload(files):
    print(files)
    for file in files:
        src_path = file.name
        dst_path = os.path.join(tmp_folder, os.path.basename(file.name))
        
        # Check if source and destination are the same
        if os.path.abspath(src_path) != os.path.abspath(dst_path):
            shutil.copy(src_path, dst_path)

        # Create a dictionary to map filename to its path
        file_mapping = {os.path.basename(file.name): file for file in files}

        # Save the dictionary as a JSON file in the tmp folder
        json_path = os.path.join(tmp_folder, "file_mapping.json")
        with open(json_path, "w") as json_file:
            json.dump(file_mapping, json_file)

with gr.Blocks(theme=gr.themes.Ocean()) as demo:
    gr.HTML("<h1 style='text-align: center;'>GEDA</h1>")
    chatbot: gr.Chatbot = gr.Chatbot(type="messages")
    msg: gr.Textbox = gr.Textbox()
    send_button: gr.Button = gr.Button("Send", variant="primary")
    file_upload: gr.File = gr.File(file_types=[".xls", ".xlsx"], file_count="multiple")
    clear: gr.Button = gr.Button("Clear Chat")

    def user(
        user_message: str, history: List[Dict[str, Any]]
    ) -> (str, List[Dict[str, Any]]):
        return "", history + [{"role": "user", "content": user_message}]

    def bot(history: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        history.append({"role": "assistant", "content": ""})
        for x in calling_agent(history[:-1]):
            if type(x) == str:  # allow llm answer stream
                history[-1]["content"] += x
            else:  # allow gradio blocks in chat
                history[-1]["content"] = x
            yield history

    msg.submit(user, [msg, chatbot], [msg, chatbot], queue=False).then(
        bot, chatbot, chatbot
    )
    send_button.click(user, [msg, chatbot], [msg, chatbot], queue=False).then(
        bot, chatbot, chatbot
    )

    clear.click(lambda: None, None, chatbot, queue=False)

    file_upload.upload(
        handle_file_upload, inputs=file_upload, outputs=None)

def main_gui() -> None:
    demo.launch()

if __name__ == "__main__":
    try:
        main_gui()
    finally:
        cleanup()  # Delete the tmp folder and file mapping JSON after the function is killed
