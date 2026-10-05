import os
import json
from dotenv import load_dotenv
from groq import Groq

load_dotenv()
client = Groq(api_key=os.getenv("GROQ_API_KEY"))
MODEL = "openai/gpt-oss-120b"
HOW_OPTIONS = ["sum", "mean", "count", "max", "min"]


# ---------- THE TOOLS ----------
# ctx holds the data (ctx["df"]) and any charts the agent makes (ctx["charts"])
def show_first_rows(ctx, n=5):
    return ctx["df"].head(int(n)).to_string()


def summary_stats(ctx):
    return ctx["df"].describe(include="all").to_string()


def group_and_aggregate(ctx, group_by, value_column, how="sum"):
    if how not in HOW_OPTIONS:
        return f"Error: 'how' must be one of {HOW_OPTIONS}."
    result = ctx["df"].groupby(group_by)[value_column].agg(how)
    return result.sort_values(ascending=False).to_string()


def add_column(ctx, new_name, column_a, operation, column_b):
    df = ctx["df"]
    if operation == "add":
        df[new_name] = df[column_a] + df[column_b]
    elif operation == "subtract":
        df[new_name] = df[column_a] - df[column_b]
    elif operation == "multiply":
        df[new_name] = df[column_a] * df[column_b]
    elif operation == "divide":
        df[new_name] = df[column_a] / df[column_b]
    else:
        return "Error: operation must be add, subtract, multiply or divide."
    return f"Added column '{new_name}'. Columns now: {list(df.columns)}"


def bar_chart(ctx, group_by, value_column, how="sum"):
    if how not in HOW_OPTIONS:
        return f"Error: 'how' must be one of {HOW_OPTIONS}."
    result = ctx["df"].groupby(group_by)[value_column].agg(how)
    ctx["charts"].append(
        {"title": f"{how} of {value_column} by {group_by}", "data": result}
    )
    return "Chart created and shown to the user."


TOOL_FUNCTIONS = {
    "show_first_rows": show_first_rows,
    "summary_stats": summary_stats,
    "group_and_aggregate": group_and_aggregate,
    "add_column": add_column,
    "bar_chart": bar_chart,
}


# ---------- THE MENU ----------
def make_tool(name, description, properties=None, required=None):
    return {
        "type": "function",
        "function": {
            "name": name,
            "description": description,
            "parameters": {
                "type": "object",
                "properties": properties or {},
                "required": required or [],
            },
        },
    }


TOOLS = [
    make_tool(
        "show_first_rows",
        "Show the first rows of the data to see its columns and values.",
        {"n": {"type": "integer", "description": "Number of rows"}},
    ),
    make_tool(
        "summary_stats",
        "Get summary statistics (count, mean, min, max, etc.) for all columns.",
    ),
    make_tool(
        "group_and_aggregate",
        "Group rows by one column and sum/average/count/max/min another column. Sorted highest to lowest.",
        {
            "group_by": {"type": "string"},
            "value_column": {"type": "string"},
            "how": {"type": "string", "enum": HOW_OPTIONS},
        },
        ["group_by", "value_column"],
    ),
    make_tool(
        "add_column",
        "Create a new column by combining two existing columns, e.g. revenue = units multiply price.",
        {
            "new_name": {"type": "string"},
            "column_a": {"type": "string"},
            "operation": {"type": "string", "enum": ["add", "subtract", "multiply", "divide"]},
            "column_b": {"type": "string"},
        },
        ["new_name", "column_a", "operation", "column_b"],
    ),
    make_tool(
        "bar_chart",
        "Draw a bar chart for the user: group by one column and sum/average/count/max/min another.",
        {
            "group_by": {"type": "string"},
            "value_column": {"type": "string"},
            "how": {"type": "string", "enum": HOW_OPTIONS},
        },
        ["group_by", "value_column"],
    ),
]

SYSTEM_PROMPT = (
    "You are a careful data analyst. Always use the tools to look at the data "
    "before answering. Never guess numbers. When a chart would help, use the bar_chart tool. "
    "Keep final answers short and clear."
)


# ---------- THE LOOP ----------
def ask_agent(df, question):
    ctx = {"df": df.copy(), "charts": []}
    steps = []
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": question},
    ]

    for _ in range(8):  # safety limit
        response = client.chat.completions.create(model=MODEL, messages=messages, tools=TOOLS)
        msg = response.choices[0].message

        if not msg.tool_calls:  # final answer
            return {"answer": msg.content, "charts": ctx["charts"], "steps": steps}

        messages.append(msg)
        for call in msg.tool_calls:
            name = call.function.name
            args = json.loads(call.function.arguments or "{}")
            steps.append(f"{name}({args})")
            try:
                result = TOOL_FUNCTIONS[name](ctx, **args)
            except Exception as e:
                result = f"Error: {e}"
            messages.append({"role": "tool", "tool_call_id": call.id, "content": str(result)})

    return {"answer": "Stopped: too many steps.", "charts": ctx["charts"], "steps": steps}