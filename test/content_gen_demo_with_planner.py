import os
from langchain.agents import tool
from src.marketing_content_gen import page_render
from src.marketing_content_gen_with_planner import (
    generate_account_summary,
    generate_company_summary,
    generate_account_marketing_pitch,
    generate_replacement_content,
    parse_company_info,
    parse_target_info,
)
from langchain.agents import initialize_agent, AgentType
from langchain.agents import Tool
from langchain.memory import ConversationBufferMemory
from langchain_openai import ChatOpenAI
from bs4 import BeautifulSoup

import json


def load_company_info(path="data/company_info.json"):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def load_target_info(path="data/target_info.json"):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def load_landing_page_html(path="data/landing_page.html"):
    with open(path, "r", encoding="utf-8") as f:
        return f.read()

# @tool
# def summarize_company_tool(company_info: dict) -> str:
#     """Summarize Stampli's services and differentiators."""
#     return generate_company_summary(company_info)

# @tool
# def summarize_account_tool(name: str, url: str) -> str:
#     """Summarize the account using its name and URL."""
#     return generate_account_summary(name, url)

# @tool
# def generate_pitch_tool(account_summary: str, company_summary: str, target_info: dict) -> str:
#     """Generate a marketing pitch from summary and target data."""
#     return generate_account_marketing_pitch(account_summary, company_summary, target_info)

# @tool
# def generate_html_tool(pitch: str, html_path: str, positions: list) -> dict:
#     """Generate HTML replacement content from pitch and structure."""
#     return generate_replacement_content(pitch, html_path, positions)


toolkit = [
    Tool.from_function(
        func=generate_replacement_content,
        name="generate_replacement_content",
        description="Generate replacement content for HTML placeholders",
    )
]

llm = ChatOpenAI(
    model="gpt-4", temperature=0.7, openai_api_key=os.getenv("OPENAI_API_KEY")
)
memory = ConversationBufferMemory(memory_key="chat_history", return_messages=True)
company_info = load_company_info()
html_template = load_landing_page_html()

# agent = initialize_agent(
#     agent=AgentType.ZERO_SHOT_REACT_DESCRIPTION,
#     tools=toolkit,
#     llm=llm,
#     memory=memory,
#     verbose=True,
# )

parsed_company_info = parse_company_info(company_info)
# print(parsed_company_info)
parsed_target_info = parse_target_info("data/target_info.json")


for account in parsed_target_info["accounts"]:
    account_name = account["name"]
    account_url = account["url"]

    # Define keys for memory lookup
    account_key = f"account_summary::{account_name}"
    pitch_key = f"marketing_pitch::{account_name}"

    # Load memory variables once
    memory_vars = memory.load_memory_variables({})

    # Step 1: Generate or retrieve account summary
    if account_key in memory_vars:
        account_summary = memory_vars[account_key]
    else:
        print(f"Generating account summary for {account_name}")
        account_summary = generate_account_summary(account_name, account_url)
        memory.chat_memory.add_ai_message(account_summary)
        memory.save_context(
            {"input": f"Summarize account: {account_name}"},
            {account_key: account_summary}
        )

    # Step 2: Generate or retrieve company summary
    if "company_summary" in memory_vars:
        company_summary = memory_vars["company_summary"]
    else:
        print("Generating company summary for Stampli")
        company_summary = generate_company_summary(parsed_company_info)
        memory.chat_memory.add_ai_message(company_summary)
        memory.save_context(
            {"input": "Summarize company profile"},
            {"company_summary": company_summary}
        )

    # Step 3: Generate or retrieve marketing pitch
    if pitch_key in memory_vars:
        account_marketing_pitch = memory_vars[pitch_key]
    else:
        print(f"Generating marketing pitch for {account_name}")
        account_marketing_pitch = generate_account_marketing_pitch(
            account_summary, company_summary, parsed_target_info
        )
        memory.chat_memory.add_ai_message(account_marketing_pitch)
        memory.save_context(
            {"input": f"Generate marketing pitch for {account_name}"},
            {pitch_key: account_marketing_pitch}
        )

    # Step 4: Define target placeholders in the HTML template
    positions = [
        {"placeholder": "hs_cos_wrapper_widget_1611686344563"},  # Main headline
        {"placeholder": "hs_cos_wrapper_banner"},                 # Banner paragraph
        {"placeholder": "hs_cos_wrapper_widget_1609866779313"}    # Subtitle
    ]

    # Step 5: Generate HTML replacement content
    print(f"Generating HTML replacement content for {account_name}")
    replacement_content = generate_replacement_content(
        account_marketing_pitch,
        "data/landing_page.html",
        positions
    )

    print(f"Replacement content for {account_name}:", replacement_content)

    # Step 6: Render the final landing page
    page_render(
        "data/landing_page.html",
        f"output/{account_name}_landing_page.html",
        replacement_content
    )
