# GEDA: Generative Excel Data Assistant

## Introduction
<!-- Context and explanation of the project. -->

### Description
GEDA (Generative Excel Data Assistant) is an intelligent Python-based assistant that uses open-source language models to interact with Excel files through natural language queries. It enables users to upload Excel files, query and manipulate data, perform complex analysis, and generate visualizations, all through a chat-like interface. GEDA leverages the power of language models to understand user intent and execute tasks using pre-defined Python functions. 

### Key Features
- **Excel File Handling:** Upload and interact with one or more Excel files.
- **Natural Language Understanding:** Interpret user prompts and execute tasks using the e.g., the XlsxWriter Python library.
- **Function Calling:** Map user intent to pre-defined Python functions for safe and effective operations.
- **Data Analysis & Visualization:** Query individual cells (TODO?), create new columns, and plot visualizations like histograms or line plots.
- **User Interface:** Minimal, chat-like interface built with Gradio.


## Documentation
<!-- What kind of prompts are supported, how to use the offline model, etc.
Screenshots of the working GEDA and its features. -->

### Installation
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

### Supported Prompts
TODO: Add supported prompts and examples from Teams Loop component. Add screenshots of the working GEDA.

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


## Details about GEDA's Backend
<!-- How the backend works, how the language model is used, etc. -->

### Our Solution
Once a query is issued by the user, GEDA starts inspecting the uploaded files and creates Panda dataframes from them. Then GEDA detects the header row to ensure accurate data extraction. The optional information that sometimes appears above the header row (title and description) is saved into an `info_text` array. Based on the file name, the header row (column names), and the rows above the header row (optional title and description), GEDA asks an LLM to analyze what the files contain and generate a `metadata` dictionary for each file, which may take some time. For time-saving purposes, GEDA caches the metadata dictionary in JSON format to save time in the future. The cached data is cleared upon restarting GEDA.

The metadata dictionary contains the following information:
- `type`: The type of data in the file (e.g., sales, inventory).
- `country_code`: The country code of the data (e.g., US, UK).
- `year_from`: The starting year of the data.
- `year_to`: The ending year of the data.
- `columns`: A dictionary mapping standardized column names to their individual column names in the corresponding files.
- `checksum`: A checksum to detect changes. If the checksum changed, the metadata is updated.

An example of a metadata dictionary is shown below:
```json
{"type": "sales", "country_code": "US", "year_from": "2020", "year_to": "2020", "columns": {"month": "Month", "material": "Material", "units_sold": "Units Sold", "total_sales_dollar": "Total Sales ($)"}, "checksum": "2ba12fb840b469a0ca71bc6c9aed061f"}
```

Next, GEDA will use an LLM to understand the user's query and map it to a predefinde function, using the function descriptions in `function_calling_agent.py`.

The function (defined in `function.py`) will find the relevant Excel files thanks to the metadata, perform the action wished by the user and return the result, which appears as a text, a table, a manipulated document (TODO?) or an interactive plot in the Gradio Chatbot window.


## Discussion of Results and Learnings
<!-- What worked well, what didn't work, what could be improved, etc. -->

We have noticed that LLMs sometimes struggle to figure out what functions to call, especially if there are functions tailored to specific prompts but they do similar things or take similar parameters. To combat this, we tried to make the function descriptions as clear as possible. However, this is not always enough. What we also did was try to make the functions as capable as possible, but at the same time, as generic as possible. This was achieved by adding more options (paramaters) but also by defining default parameters if no information for them is provided and, thus, making the function as flexible as possible. This way, the LLM can call the same function for similar tasks, which makes it easier for the LLM to understand what to do, and there is not much redundant code since there are no longer multiple functions doing almost the same thing.

For example, a function made to fulfill the prompt "Plot the evolution of sales for every month in Switzerland for 2023" should not only do exactly that but should also be able to accept a specific month range and should be able to convert the currency of the resulting data to whatever the user wishes. If the user additionally wants to see the evolution for a specific material only, the function should also be able to handle it. This way, the function can also fulfill "Plot the evolution of sales of Steel from January to June in Switzerland for 2023 for wood in Euro."

We learned that there is a lot to engineer around the AI and that GEDA is only as capable as the "tools" (as in the functions) we provide it with.