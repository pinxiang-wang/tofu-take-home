from langchain.prompts import PromptTemplate
from langchain_community.chat_models import ChatOpenAI
from langchain.chains import LLMChain


# Define the company info prompt
def get_company_info_prompt():
    return PromptTemplate.from_template(
        """You are a business analyst AI.

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
"""
    )

# Define the target info prompt
def get_target_info_prompt():
    return PromptTemplate.from_template(
        """You are a sales enablement assistant.

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
"""
    )

# Create chains for each prompt
def create_company_chain(llm):
    return LLMChain(prompt=get_company_info_prompt(), llm=llm)

def create_target_chain(llm):
    return LLMChain(prompt=get_target_info_prompt(), llm=llm)
