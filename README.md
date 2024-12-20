# GEDA: Generative Excel Data Assistant

> Made with ♥ by Dominik Rüegg, Thomas Rüegg, Patrick Wissiak

## Description

GEDA (Generative Excel Data Assistant) is an intelligent Python-based assistant that uses open-source language models to interact with Excel files through natural language queries. It enables users to upload Excel files, query and manipulate data, perform complex analysis, and generate visualizations, all through a chat-like interface. GEDA leverages the power of language models to understand user intent and execute tasks using pre-defined Python functions.

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

### Usage of Offline Model

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
