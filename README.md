# GEDA: Generative Excel Data Assistant

**Description:**  
GEDA (Generative Excel Data Assistant) is an intelligent Python-based assistant that uses open-source language models to interact with Excel files through natural language queries. It enables users to upload Excel files, query and manipulate data, perform complex analysis, and generate visualizations, all through a chat-like interface.

## Key Features
- **Excel File Handling:** Upload and interact with one or more Excel files.
- **Natural Language Understanding:** Interpret user prompts and execute tasks using supported Python libraries (e.g., OpenPyXL, XlsxWriter).
- **Function Calling:** Map user intent to pre-defined Python functions for safe and effective operations.
- **Data Analysis & Visualization:** Query individual cells, create new columns, and plot visualizations like histograms or line plots.
- **User Interface:** Minimal, chat-like interface built with frameworks like Gradio or Streamlit.

## Installation
1. Clone the repository:
    ```bash
    git clone <repo link>
    ```
2. Install the required packages:
    ```bash
    pip install -r requirements.txt
    ```
3. Rename the `.env.example` file to `.env` and update the environment variables.
4. Run the application:
    ```bash
    python gui.py
    ```
5. Access the web interface at `http://localhost:7860`.

## Usage of Offline Model
1. Download Ollama [here](https://ollama.com/).
2. Open a command prompt and download the model:
    ```bash
    ollama pull llama3.2
    ```
3. Start the Ollama server:
    ```bash
    ollama serve
    ```
4. Make sure the environment variable `MODEL_NAME` is set to the model name:
    ```bash
    MODEL_NAME="llama3.2" 
    ```
