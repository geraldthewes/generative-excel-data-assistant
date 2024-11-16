import gradio as gr
import pandas as pd
import os
import shutil
from function_calling_agent import FunctionAgent
from llm_factory import llm_factory
from typing import List, Dict, Any
from datetime import datetime

llm = llm_factory("llmhub")
calling_agent = FunctionAgent(llm)

# Define the tmp folder
tmp_folder = os.path.join(os.getcwd(), "tmp")

# Function to clean up the tmp folder after program ends
def cleanup():
    if os.path.exists(tmp_folder):
        shutil.rmtree(tmp_folder)

# Ensure tmp folder exists
if not os.path.exists(tmp_folder):
    os.makedirs(tmp_folder)

with gr.Blocks() as demo:
    chatbot: gr.Chatbot = gr.Chatbot(type="messages")
    msg: gr.Textbox = gr.Textbox()
    file_upload: gr.File = gr.File(file_types=[".xls", ".xlsx"], file_count="multiple")
    clear: gr.Button = gr.Button("Clear Chat")
        
    def user(user_message: str, history: List[Dict[str, Any]]) -> (str, List[Dict[str, Any]]):
        return "", history + [{"role": "user", "content": user_message}]

    def bot(history: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        history.append({"role": "assistant", "content": ""})
        for x in calling_agent(history[:-1]):
            history[-1]["content"] += x
            yield history

    msg.submit(user, [msg, chatbot], [msg, chatbot], queue=False).then(
        bot, chatbot, chatbot
    )
    clear.click(lambda: None, None, chatbot, queue=False)
    
    file_upload.upload(
        lambda files: [shutil.copy(file.name, tmp_folder) for file in files],
        inputs=file_upload,
        outputs=[]
    )

def main_gui() -> None:
    demo.launch()

if __name__ == "__main__":
    try:
        main_gui()
    finally:
        cleanup()  # Delete the tmp folder after the function is killed
