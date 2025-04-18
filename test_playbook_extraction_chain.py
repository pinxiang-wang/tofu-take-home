from langchain_openai import ChatOpenAI
from langchain.prompts import PromptTemplate
import os
import json

# Define prompt template
company_prompt = PromptTemplate.from_template("""
You are a business analyst AI.

Given a JSON-formatted company profile, extract and summarize the following fields:

- Company Name
- Company Website
- AP Automation Link
- Product Overview
- Official Overview
- Company Description
- Key Differentiators

Please return a well-structured English summary in this format:

Company Info Summary:
Company Name: {{company_name}}
AP Automation: {{ap_automation}}
Company Website: {{website}}
Product Overview: {{product_overview}}
Official Overview: {{official_overview}}
Company Description: {{description}}
Stampli Differentiators: {{differentiators}}

Input:
{json_input}
""")

target_prompt = PromptTemplate.from_template("""
You are a sales enablement assistant.

Given a JSON file describing customer targets, extract and organize the information into four categories:

1. Accounts (name + website)
2. Personas (title + description + link)
3. Industries (name + summary + link)
4. Healthcare Subverticals (name + description + link)

Format the output in readable markdown, with categories separated and each item shown in this style:

- [Accounts] YMCA: https://www.ymca.org/
- [Personas] CFO: <short description>. <link>
- [Industries] Healthcare: <industry description>. <link>

If any category has no data, skip it.

Input JSON:
{json_input}
""")

# Create LLM
llm = ChatOpenAI(
    temperature=0.2,
    model="gpt-4o",  # ✅ 你现在可以使用 gpt-4o
)

# Create runnable chains
company_chain = company_prompt | llm
target_chain = target_prompt | llm

if __name__ == "__main__":
    with open("company_info.json", "r") as f:
        company_info_json = f.read()

    with open("target_info.json", "r") as f:
        target_info_json = f.read()

    company_summary = company_chain.invoke({"json_input": company_info_json})
    target_summary = target_chain.invoke({"json_input": target_info_json})

    with open("company_info_summary.txt", "w") as f:
        f.write(company_summary.content)

    with open("target_info_summary.txt", "w") as f:
        f.write(target_summary.content)

    print("✅ Summaries written to disk.")
