# 📊 Data Analyst Agent

An AI agent that analyzes any CSV file. Upload your data, ask questions in plain English, and the agent runs the analysis and draws charts for you.

**Live demo:** ADD_YOUR_STREAMLIT_LINK_HERE

## What it does
- Upload any CSV and ask questions like "Which region made the most revenue?"
- The agent picks the right tools, runs them, and explains the result
- Draws bar charts automatically
- Shows every step it took, so you can check its work

## How it works
The agent has a **brain** (an LLM), **tools** (Python/pandas functions), and a **loop**: it thinks, uses a tool, reads the result, and repeats until it has an answer.

Tools: show rows, summary statistics, group and aggregate, create new column, bar chart.

## Tech stack
Python, pandas, Streamlit, Groq API (openai/gpt-oss-120b)

## Run it yourself
```bash
pip install -r requirements.txt
```
Create a `.env` file with your free key from console.groq.com:
```
GROQ_API_KEY=your_key_here
```
Then run:
```bash
python -m streamlit run app.py
```

## Screenshot
ADD_A_SCREENSHOT_HERE