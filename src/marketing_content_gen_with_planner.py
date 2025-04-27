from langchain.agents import initialize_agent
from langchain.memory import ConversationSummaryBufferMemory
from langchain.chat_models import ChatOpenAI
from langchain.schema import SystemMessage, HumanMessage
from langchain.text_splitter import TokenTextSplitter
from langchain.callbacks import get_openai_callback
from bs4 import BeautifulSoup
from src.marketing_content_gen import preview_conversation
import tiktoken
import time
import json

llm = ChatOpenAI(temperature=0.5, model="gpt-3.5-turbo")

CHUNK_TOKEN_SIZE = 3900
SUMMARY_TARGET_LENGTH = 500  # words
RETRY_ATTEMPTS = 3
TARGET_PITCH_LENGTH = 2500  # words

def parse_company_info(company_info_json):
    """
    Parse the company_info.json file to extract essential company knowledge.

    Args:
        company_info_json (dict): Dictionary loaded from company_info.json.

    Returns:
        dict: Parsed dictionary containing key company summary fields.
    """
    fields_to_extract = [
        "Company Name",
        "Company Website",
        "Company Description",
        "Official Overview ",
        "Product Overview",
        "Stampli differentiators",
        "AP Automation",
    ]

    parsed_info = {}
    for field in fields_to_extract:
        if field in company_info_json and "data" in company_info_json[field]:
            # Concatenate multiple entries if exist
            values = [
                item["value"]
                for item in company_info_json[field]["data"]
                if "value" in item
            ]
            parsed_info[field.strip()] = "\n".join(values)

    return parsed_info


def parse_target_info(filepath):
    """
    Parse the target_info.json file and separate Accounts, Industries, and Personas.

    Args:
        filepath (str): Path to the target_info.json file.

    Returns:
        dict: {
            "accounts": List[{"name": str, "url": str}],
            "industries": List[{"name": str, "description": str, "url": str}],
            "personas": List[{"name": str, "description": str, "url": str}]
        }
    """
    with open(filepath, "r", encoding="utf-8") as file:
        data = json.load(file)

    parsed = {"accounts": [], "industries": [], "personas": []}

    # Extract accounts
    for name, details in data.get("Accounts", {}).items():
        if name == "meta":
            continue
        url = ""
        for entry in details.get("data", []):
            if entry["type"] == "url":
                url = entry["value"]
        parsed["accounts"].append({"name": name, "url": url})

    # Extract industries
    for name, details in data.get("Industries", {}).items():
        if name == "meta":
            continue
        description = ""
        url = ""
        for entry in details.get("data", []):
            if entry["type"] == "text":
                description = entry["value"]
            elif entry["type"] == "url":
                url = entry["value"]
        parsed["industries"].append(
            {"name": name, "description": description, "url": url}
        )

    # Extract personas
    for name, details in data.get("Personas", {}).items():
        if name == "meta":
            continue
        description = ""
        url = ""
        for entry in details.get("data", []):
            if entry["type"] == "text":
                description = entry["value"]
            elif entry["type"] == "url":
                url = entry["value"]
        parsed["personas"].append(
            {"name": name, "description": description, "url": url}
        )

    return parsed


def generate_account_summary(account_name: str, url: str) -> str:
    """
    Generates a summary of the account using its name and website URL.

    Args:
        account_name (str): The name of the company or organization.
        url (str): The official URL of the company.

    Returns:
        str: A concise summary of the company or organization.
    """
    # Prompt setup
    system_msg = SystemMessage(
        content="You are an expert business analyst who summarizes companies' missions and services based on their name and official URL."
    )

    human_msg = HumanMessage(
        content=f"""Company Name: {account_name}
        Company Website: {url}

        Please generate a concise summary of this company or organization. The summary should:
        - Be 100–300 words.
        - Explain the company's core services or mission.
        - Reflect the tone appropriate to the company type (non-profit, corporate, etc).
        - Optionally suggest why it might benefit from automated AP solutions like Stampli.

        Respond only with the plain summary text. Do NOT use JSON formatting.
        """
    )

    # Invoke the LLM
    response = llm.invoke([system_msg, human_msg])

    return response.content.strip()

def num_tokens_from_string(string: str, encoding_name: str = "cl100k_base") -> int:
    encoding = tiktoken.get_encoding(encoding_name)
    return len(encoding.encode(string))


def split_into_chunks(text: str, chunk_token_size: int = CHUNK_TOKEN_SIZE):
    splitter = TokenTextSplitter(chunk_size=chunk_token_size, chunk_overlap=100)
    return splitter.split_text(text)

def summarize_chunk(chunk: str, chunk_ratio: float, attempt=1) -> str:
    """
    Summarizes a given text chunk using OpenAI's language model, with a proportionally allocated word count.

    Args:
        chunk (str): The chunk of text to summarize.
        chunk_ratio (float): The proportion of this chunk relative to the total input (used to scale target summary length).
        attempt (int): Internal use for retry logic.

    Returns:
        str: The summary of the chunk.
    """
    estimated_words = int(500 * chunk_ratio)  # Target ~500 words total, so this chunk gets a proportion
    messages = [
        SystemMessage(content="You are a helpful assistant specialized in summarizing company profiles."),
        HumanMessage(content=(
            f"Please summarize the following content clearly and concisely.\n"
            f"The summary should be approximately {estimated_words} words to match the proportional length "
            f"relative to the full document:\n\n{chunk}"
        ))
    ]

    try:
        response = llm.invoke(messages)
        return response.content.strip()
    except Exception as e:
        if attempt < 3:
            print(f"Retrying summarization (attempt {attempt + 1}) due to error: {e}")
            return summarize_chunk(chunk, chunk_ratio, attempt + 1)
        else:
            print(f"Failed to summarize chunk after 3 attempts. Returning fallback.")
            return f"[Summary unavailable for this section due to error: {e}]"

def generate_company_summary(parsed_company_info: dict) -> str:
    """
    Generate a concise summary (~500 words) of a company's profile based on structured parsed input.

    Args:
        parsed_company_info (dict): Dictionary containing structured company fields and their values.

    Returns:
        str: Final polished company summary.
    """
    # Step 1: Extract relevant text fields from the dictionary
    combined_text = "\n\n".join([f"{k}:\n{v}" for k, v in parsed_company_info.items()])

    print(combined_text)
    # print("---- Combined Company Info ----")
    # print(combined_text[:1000] + "..." if len(combined_text) > 1000 else combined_text)
    # print("---- End of Company Info ----")

    # Step 2: Token length check and split
    chunks = split_into_chunks(combined_text, CHUNK_TOKEN_SIZE)

    chunk_token_counts = [num_tokens_from_string(c) for c in chunks]
    total_tokens = sum(chunk_token_counts)

    all_summaries = []
    for idx, (chunk, token_count) in enumerate(zip(chunks, chunk_token_counts)):
        chunk_ratio = token_count / total_tokens
        print(f"Summarizing chunk {idx + 1}/{len(chunks)}... (Ratio: {chunk_ratio:.2f})")
        summary = summarize_chunk(chunk, chunk_ratio)
        all_summaries.append(summary)

    # Step 3: Combine and polish
    combined_summary_prompt = "\n".join(all_summaries)
    final_messages = [
        SystemMessage(content="You are a helpful assistant that creates polished summaries of business information."),
        HumanMessage(content=(
            f"Combine the following summaries into a single cohesive company profile.\n"
            f"The final summary should be around {SUMMARY_TARGET_LENGTH} words:\n\n{combined_summary_prompt}"
        ))
    ]

    try:
        final_result = llm.invoke(final_messages)
        return final_result.content.strip()
    except Exception as e:
        print(f"Failed to generate final summary: {e}")
        return "[Error generating final summary]"


def generate_account_marketing_pitch(
    account_summary: str,
    company_summary: str,
    parsed_target_info: dict
) -> str:
    """
    Generate a marketing pitch for a target account using account summary,
    company summary, and full target information.
    
    Parameters:
        account_summary (str): Summary of the target account (YMCA).
        company_summary (str): Summary of Stampli's core services and capabilities.
        parsed_target_info (dict): A structured dict containing 'accounts', 'industries', and 'personas'.

    Returns:
        str: A ~2000-word marketing pitch tailored to the account.
    """
    industry_summaries = {
        industry["name"]: industry["description"]
        for industry in parsed_target_info["industries"]
        if industry.get("description")
    }

    persona_summaries = {
        persona["name"]: persona["description"]
        for persona in parsed_target_info["personas"]
        if persona.get("description")
    }

    conversation = [
        SystemMessage(content=(
            "You are a senior marketing strategist. Your job is to analyze business descriptions and generate "
            "precise, strategic, and compelling marketing pitches. Avoid generic content. All statements must be grounded "
            "in the account's needs and Stampli's service capabilities."
        )),
        HumanMessage(content=(
            "Here is Stampli's overall company summary that describes its capabilities and value proposition:\n"
            f"{company_summary}"
        )),
        HumanMessage(content=(
            "Here is a description of the target account:\n"
            f"{account_summary}"
        )),
        HumanMessage(content=(
            "Here is the list of industry-specific services offered by Stampli:\n\n" +
            "\n\n".join([f"Industry - {k}:\n{v}" for k, v in industry_summaries.items()])
        )),
        HumanMessage(content=(
            "Here is the list of persona-specific services offered by Stampli:\n\n" +
            "\n\n".join([f"Persona - {k}:\n{v}" for k, v in persona_summaries.items()])
        )),
        HumanMessage(content=(
            "Please classify the account into the most relevant Industry and Persona based on the descriptions provided.\n"
            "Emphasize the challenges of that Industry and the needs of that Persona.\n"
            "Then generate a tailored marketing pitch no less than 2000 words addressing how Stampli can serve this account best.\n"
            "Maintain an informative and persuasive tone—be a strategic advisor, not a salesperson.\n"
            "Be clear of those fields and attack these entities directly by the end of the marketing pitch:\n"
            "1. Account Name\n"
            "2. Industry\n"
            "3. Persona\n"
            "4. Account's Services\n"
            "5. Generated Content Length\n"
        ))
    ]
    # conversation_content = preview_conversation(conversation)
    # print(conversation_content)
    for attempt in range(1, RETRY_ATTEMPTS + 1):
        try:
            result = llm.invoke(conversation)
            pitch = result.content.strip()
            print("pitch: ", pitch)
            return pitch
            
        except Exception as e:
            print(f"Error during generation: {e}. Retrying in 3 seconds...")
            time.sleep(3)

    raise RuntimeError("Failed to generate a valid marketing pitch after multiple attempts.")


def generate_replacement_content(pitch_text: str, html_path: str, positions: list) -> dict:
    with open(html_path, "r", encoding="utf-8") as f:
        soup = BeautifulSoup(f.read(), "html.parser")

    tag_infos = []
    for pos in positions:
        placeholder = pos["placeholder"]
        tag = soup.find(id=placeholder)
        if tag:
            original_text = tag.get_text(strip=True)
            html_snippet = str(tag)
            tag_infos.append({
                "placeholder": placeholder,
                "original": original_text,
                "length": len(original_text),
                "html": html_snippet
            })

    # Step 3: Build final instruction for GPT to generate the replacement content
    final_instruction = (
        f"The reference pitch is:\n\n{pitch_text}\n\n"
        "make full use of this background knowledge, your task is to generate concise replacement content for each of "
        "the following HTML placeholders.\n"
        "The title should be attention-grabbing and relevant to the account.\n"
        "For all replacements, please ensure the content length is approximately similar to the original content length "
        "to preserve the visual layout of the landing page.\n"
        "The content should integrate the following critical details:\n"
        "  1. The target audience is the an account name, industry, or a persona. They are independent of each other. Any of them can be the target audience.\n"
        "  2. The content should be of approximately the same length as the original content to preserve the layout. And the logic of the content should be the same as the marketing pitch.\n"
        "  3. Don't get misled by the original content, the content should be tailored to the target audience.\n"
        "     The original content is just for a logic, structural and length reference. It may not be the actual content for the target audience.\n"
        "Respond using the following format:\n"
        "REPLACEMENT for <placeholder>: <content>\n\n"
        "Here are the HTML sections that need replacement:\n"
    )

    # Loop over each placeholder and add its details
    for t in tag_infos:
        final_instruction += f"- Placeholder: {t['placeholder']}\n"
        final_instruction += f"  HTML snippet to preserve (structure only):\n"
        final_instruction += f"  {t['html']}\n"
        final_instruction += f"  Text content to replace: \"{t['original']}\" (about {t['length']} characters), remember to keep the same length and logic as the marketing pitch.\n"    
  
    

    # Call LLM
    messages = [
        SystemMessage(content="You are a helpful assistant for marketing to help user's HTML content customization."),
        SystemMessage(content=final_instruction),
    ]

    result = llm.invoke(messages)

    # Parse response
    replacement_dict = {}

    for line in result.content.splitlines():
        if line.startswith("REPLACEMENT for "):
            try:
                key, value = line.split(":", 1)
                key = key.replace("REPLACEMENT for", "").strip()
                value = value.strip()
                replacement_dict[key] = value
            except ValueError:
                continue

    return replacement_dict