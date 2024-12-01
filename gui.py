import gradio as gr
import pandas as pd
import os
import shutil
from function_calling_agent import FunctionAgent
from llm_factory import llm_factory
from typing import List, Dict, Any
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

llm = llm_factory(os.getenv("MODEL_NAME", ""))
calling_agent = FunctionAgent(llm)

# Define the tmp folder
tmp_folder = os.path.join(os.getcwd(), "tmp")

# Function to clean up the tmp folder after program ends
def cleanup():
    if os.path.exists(tmp_folder):
        shutil.rmtree(tmp_folder)
    os.mkdir(tmp_folder)

# Ensure tmp folder exists
if not os.path.exists(tmp_folder):
    os.makedirs(tmp_folder)

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
        lambda files: [shutil.copy(file.name, tmp_folder) for file in files],
        inputs=file_upload,
        outputs=[],
    )

def main_gui() -> None:
    demo.launch()

if __name__ == "__main__":
    cleanup()  # Delete the tmp folder after the function is killed
    main_gui()
