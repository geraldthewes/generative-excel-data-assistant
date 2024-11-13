import gradio as gr
from function_calling_agent import FunctionAgent
from llm_factory import llm_factory

llm = llm_factory("llmhub")

llm = FunctionAgent(llm)

with gr.Blocks() as demo:
    chatbot = gr.Chatbot(type="messages")
    msg = gr.Textbox()
    clear = gr.Button("Clear")

    def user(user_message, history: list):
        return "", history + [{"role": "user", "content": user_message}]

    def bot(history: list):
        history.append({"role": "assistant", "content": ""})
        for x in llm(history[:-1]):
            history[-1]["content"] += x
            yield history

    msg.submit(user, [msg, chatbot], [msg, chatbot], queue=False).then(
        bot, chatbot, chatbot
    )
    clear.click(lambda: None, None, chatbot, queue=False)

def main_gui():
    demo.launch()

if __name__ == "__main__":
    main_gui()