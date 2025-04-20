import json
import openai
import os
from bs4 import BeautifulSoup, NavigableString
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain
from langchain_openai import ChatOpenAI
from langchain.schema import HumanMessage, SystemMessage
from langchain.text_splitter import RecursiveCharacterTextSplitter


# Initialize the GPT model
llm = ChatOpenAI(temperature=0.4, model="gpt-4o")
ATTEMPTS = 10

# Function to fetch and summarize URL content using LangChain through OpenAI
def parse_account_url_with_langchain(account_url: str, max_length=1500) -> str:
    try:
        # Create a prompt template for LangChain
        prompt_template = f"""
        Given the URL: {account_url}, summarize the content of the webpage into a short description. 
        Focus on key information about the company, its products, and services, no longer than {max_length} characters.
        """

        # Create the LangChain with the prompt template
        prompt = PromptTemplate(
            input_variables=["account_url"], template=prompt_template
        )
        chain = LLMChain(llm=llm, prompt=prompt)

        # Call LangChain to generate the content
        result = chain.run(account_url=account_url)

        # Ensure the result does not exceed the maximum length
        if len(result) > max_length:
            result = result[:max_length]  # Truncate if needed

        return result

    except openai.error.OpenAIError as e:
        print(f"Error with OpenAI API: {e}")
        return ""


# Split long text into chunks
def chunk_text(text, max_tokens=3900):
    splitter = RecursiveCharacterTextSplitter(chunk_size=max_tokens, chunk_overlap=100)
    return splitter.split_text(text)


def validate_replacement_content(replacements_dict, account_name):
    """
    Validate that the Account Name is included in the replacements dictionary.
    This function checks if the Account Name appears in any of the replacement values.
    """
    for key, value in replacements_dict.items():
        if account_name in value:
            return True  # Account Name found in the replacement content
    return False  # Account Name not found


# Generate the prompt for GPT
def generate_prompt(account_name, account_knowledge, industry_chunks, persona_chunks):
    return f"""
    Given the account description, persona and industry descriptions, classify the client into the best matching industry and persona, and generate a marketing pitch for this account.
    
    Account Name: {account_name}
    Account Knowledge: {account_knowledge}
    
    Industry Descriptions:
    {', '.join(industry_chunks)}
    
    Persona Descriptions:
    {', '.join(persona_chunks)}
    
    Please output the most relevant industry and persona, and generate a marketing pitch.
    """


# Generate landing page content with chunked context
def generate_marketing_pitch(account_info, industry_descriptions, persona_descriptions):
    account_name = account_info["name"]
    account_url = account_info["context"]

    # Step 1: Extract and chunk the account knowledge
    account_knowledge = parse_account_url_with_langchain(
        account_url
    )  # Assumes HTML parsed cleanly
    account_chunks = chunk_text(account_knowledge)

    # Step 2: Chunk industry and persona descriptions
    industry_chunks = chunk_text(
        " ".join([d["context"] for d in industry_descriptions])
    )
    persona_chunks = chunk_text(" ".join([d["context"] for d in persona_descriptions]))

    # Step 3: Initialize conversation
    conversation = [
        SystemMessage(content="You are an expert in marketing content generation."),
        HumanMessage(
            content=(
                "I will provide the account background and relevant persona/industry descriptions in several parts.\n"
                "Please wait until I indicate that all parts have been submitted before replying.\n"
                "Respond only after receiving the final instruction."
            )
        ),
        HumanMessage(content=f"Account Name: {account_name}"),
        HumanMessage(content=f"Account URL: {account_url}"),
    ]

    # Step 4: Add account knowledge
    for idx, chunk in enumerate(account_chunks):
        conversation.append(
            HumanMessage(content=f"[Account Description - Part {idx+1}]:\n{chunk}")
        )

    # Step 5: Add industry description
    for idx, chunk in enumerate(industry_chunks):
        conversation.append(
            HumanMessage(content=f"[Industry Descriptions - Part {idx+1}]:\n{chunk}")
        )

    # Step 6: Add persona description
    for idx, chunk in enumerate(persona_chunks):
        conversation.append(
            HumanMessage(content=f"[Persona Descriptions - Part {idx+1}]:\n{chunk}")
        )

    # Step 7: Final instruction
    final_instruction = (
        "Now that you've received the full account information and descriptions,\n"
        "please classify this account into the most relevant Industry and Persona.\n"
        "Use the provided descriptions of our target industries and personas to determine the best match.\n"
        "Once you've identified the most relevant Industry and Persona, make sure to emphasize them in the generated content.\n"
        "The goal is to tailor the marketing pitch based on the **Persona** and **Industry** of this account.\n"
        "Generate a customized and compelling marketing pitch for this account, "
        "ensuring that the tone is appropriate for the account's persona and industry. "
        "This content should be concise, engaging, and reflect the unique challenges and needs of the account's persona and industry.\n"
        "Make sure to showcase how the services offered can directly benefit the account's persona and industry context.\n"
        "This content is displayed on a landing page, so it should be concise and engaging. "
        "Don't sound like a salesperson, but rather like a trusted advisor.\n"
        "Please focus on **highlighting the specific needs** of the selected **Persona** and **Industry**, "
        "and how the solution offered can address those needs in a meaningful way.\n"
        "Generate marketing material in around 2000 words, with particular focus on:\n"
    )

    # validate the content of the conversation sent to model:
    # print(f"Conversation: {conversation}")

    conversation.append(HumanMessage(content=final_instruction))
    preview_conversation(conversation)

    # Step 8: Run the chat model
    result = llm.invoke(conversation)

    # with open("logs/marketing_pitch.txt", "w", encoding="utf-8") as f:
    #     f.write(result.content)
    return result.content


def preview_conversation(conversation):
    """
    Join all conversation messages into one readable string for inspection.
    Saves the full prompt content into a log file for verification.
    """
    preview_text = ""
    for message in conversation:
        role = message.type if hasattr(message, "type") else message.__class__.__name__
        content = message.content
        preview_text += f"\n--- {role.upper()} ---\n{content}\n"

    return preview_text


def extract_label_contexts(html_path, positions):
    """
    Given an HTML path and a list of replacement definitions, extract the original
    content and structural context for each placeholder (e.g., tag, id).
    """
    with open(html_path, "r", encoding="utf-8") as f:
        html = f.read()
        soup = BeautifulSoup(html, "html.parser")

    result = []
    for r in positions:
        placeholder = r["placeholder"]
        purpose = r.get("purpose", "")

        tag = soup.find(id=placeholder) or soup.find(placeholder)
        if not tag:
            print(f"Could not find tag for placeholder: {placeholder}")
            continue

        content = tag.get_text(strip=True)
        length = len(content)

        result.append(
            {
                "placeholder": placeholder,
                "original": content,
                "length": length,
                "purpose": purpose,
            }
        )
    return result


def replacement_content_gen(
    account_info,
    industry_descriptions,
    persona_descriptions,
    positions,
    input_html_path,
):
    account_name = account_info["name"]
    account_url = account_info["context"]

    # Step 1: Extract and chunk the account knowledge
    account_knowledge = parse_account_url_with_langchain(account_url)
    account_chunks = chunk_text(account_knowledge)

    # Step 2: Chunk industry and persona descriptions
    industry_chunks = chunk_text(
        " ".join([d["context"] for d in industry_descriptions])
    )
    persona_chunks = chunk_text(" ".join([d["context"] for d in persona_descriptions]))

    # Step 3: Parse HTML and prepare content info from labels
    with open(input_html_path, "r", encoding="utf-8") as f:
        soup = BeautifulSoup(f.read(), "html.parser")

    tag_infos = []
    for p in positions:
        tag = soup.find(id=p["placeholder"])
        if tag:
            content = tag.get_text(strip=True)
            html_snippet = str(tag)  # This will give you the full HTML for the tag

            tag_infos.append(
                {
                    "placeholder": p["placeholder"],
                    "original": content,
                    "length": len(content),
                    "html": html_snippet,  # Ensure the 'html' field is included
                }
            )

    # Step 4: Build conversation
    conversation = [
        SystemMessage(
            content=(
                "You are an expert in marketing content generation.\n"
                "I will provide account details, industry descriptions, and persona descriptions in several parts.\n"
                "Your task will be to generate customized content for specific HTML placeholders. "
                "For each placeholder, replace only the content inside the HTML tags (e.g., <h1>, <p>, etc.), "
                "while preserving the original HTML structure (e.g., nested tags like <span>, <br> should be preserved). "
                "Ensure that the length of the new content is similar to the original content to maintain the layout."
            )
        ),
        HumanMessage(
            content=(
                "I will provide the account background and relevant persona/industry descriptions in several parts.\n"
                "Please wait until I indicate that all parts have been submitted before replying.\n"
                "Respond only after receiving the final instruction."
            )
        ),
        HumanMessage(content=f"Account Name: {account_name}"),
        HumanMessage(content=f"Account URL: {account_url}"),
    ]

    # Add account information
    for idx, chunk in enumerate(account_chunks):
        conversation.append(
            HumanMessage(content=f"[Account Description - Part {idx+1}]:\n{chunk}")
        )
    # Add industry descriptions
    for idx, chunk in enumerate(industry_chunks):
        conversation.append(
            HumanMessage(content=f"[Industry Descriptions - Part {idx+1}]:\n{chunk}")
        )
    # Add persona descriptions
    for idx, chunk in enumerate(persona_chunks):
        conversation.append(
            HumanMessage(content=f"[Persona Descriptions - Part {idx+1}]:\n{chunk}")
        )

    final_instruction_system = (
        "You are an expert in marketing content generation.\n"
        "You will be given detailed information about an account, its industry, and its persona.\n"
        "Your task is to classify the account into the most relevant industry and persona, and generate tailored content accordingly.\n"
        "Your response must respect the original content structure and logical relationships in the HTML document provided.\n"
        "Here are some key rules to follow:\n"
        "1. **Maintain the original content structure**: Ensure that the replacement content follows the same logical structure as the original, such as intro followed by supporting points.\n"
        "2. **Incorporate background knowledge**: Use the provided account, industry, and persona descriptions to guide your content generation. Match the tone and message style to the specific persona’s role (e.g., CFO, Manager).\n"
        "3. **Content length**: The replacement content must be of approximately the same length as the original content to preserve the page layout.\n"
        "4. **Understand HTML tags**: Pay special attention to the HTML tag structure. For <h1>, <h2>, <p>, <ul>, <ol>, and <a> tags, follow these rules:\n"
        "   - **<h1>, <h2>**: Craft titles and headings that are attention-grabbing and directly relevant to the account.\n"
        "   - **<p>**: Write concise paragraphs that reflect the challenges the account faces and how your services help solve them.\n"
        "   - **<ul>, <ol>**: If there are lists, each item should present a value proposition, feature, or benefit related to the account’s needs.\n"
        "   - **<a>**: Ensure the links lead to actionable results, like calls to action or further exploration."
    )

    final_instruction_human = (
        "Now that you've received the full account information and descriptions,\n"
        "please classify this account into the most relevant Industry and Persona.\n"
        "Use the provided descriptions of our target industries and personas to determine the best match.\n"
        "Then, generate a customized and compelling marketing pitch for this account,\n"
        "tailored to the account's needs and preferences.\n"
        "Next, create concise and relevant replacement content for each of the following HTML placeholders.\n"
        "For all replacements, please ensure the content length is approximately similar to the original,\n"
        "so the visual layout of the landing page is preserved.\n"
        "Respond using the following format:\n"
        "REPLACEMENT for <placeholder>: <content>\n\n"
        "Here are the HTML sections that need replacement:\n"
    )

    # Loop over each placeholder and add its details
    for t in tag_infos:
        final_instruction_human += f"- Placeholder: {t['placeholder']}\n"
        final_instruction_human += f"  HTML snippet to preserve (structure only):\n"
        final_instruction_human += f"  {t['html']}\n"
        final_instruction_human += f"  Text content to replace: \"{t['original']}\" (about {t['length']} characters)\n"
        final_instruction_human += f"  Focus: Please only replace the content within the tag, preserving the HTML structure (e.g., <h1>, <p>, etc.).\n"
        final_instruction_human += f"  Please maintain the length of the content as close as possible to the original to preserve the layout.\n"

    # Add the final instruction to the conversation
    conversation.append(HumanMessage(content=final_instruction_system))
    conversation.append(HumanMessage(content=final_instruction_human))
    # Step 5: Run the model
    result = llm.invoke(conversation)

    # Step 6: Extract replacements from result
    replacements_dict = {}
    for line in result.content.splitlines():
        if line.startswith("REPLACEMENT for "):
            try:
                key, value = line.split(":", 1)
                key = key.replace("REPLACEMENT for", "").strip()
                value = value.strip()
                replacements_dict[key] = value
            except ValueError:
                continue

    # Save the replacements_dict to a json file
    with open("logs/replacements_dict.json", "w", encoding="utf-8") as f:
        json.dump(replacements_dict, f, ensure_ascii=False, indent=4)

    return replacements_dict


def replacement_content_gen_with_pitch(
    account_info,
    industry_descriptions,
    persona_descriptions,
    positions,
    input_html_path,
):
    """
    This function generates a marketing pitch using the account, industry, and persona descriptions
    and then uses the generated pitch to guide the generation of replacement content for HTML placeholders.
    The content is then returned as a dictionary of replacements for the placeholders in the HTML.

    Args:
        account_info (dict): The account information, including name and URL.
        industry_descriptions (list): A list of industry descriptions.
        persona_descriptions (list): A list of persona descriptions.
        positions (list): A list of placeholders (HTML tags) to replace.
        input_html_path (str): The path to the input HTML template.

    Returns:
        dict: A dictionary containing the replacements for each placeholder.
    """
    log = "---------Content Generation Log---------\n"
    log = "account_info: " + str(account_info) + "\n"
    # log += "industry_descriptions: " + str(industry_descriptions) + "\n"
    log += "persona_descriptions: " + str(persona_descriptions) + "\n"
    log += "positions: " + str(positions) + "\n"
    log += "input_html_path: " + str(input_html_path) + "\n"
    log += "-----------------------------------------\n"
    # Step 1: Generate marketing pitch using generate_landing_page
    marketing_pitch = generate_marketing_pitch(
        account_info, industry_descriptions, persona_descriptions
    )
    log += f"Marketing Pitch: {marketing_pitch}\n"
    # with open("logs/marketing_pitch.txt", "w", encoding="utf-8") as f:
    #     f.write(marketing_pitch)

    # Step 2: Parse the HTML and prepare content info from labels
    with open(input_html_path, "r", encoding="utf-8") as f:
        soup = BeautifulSoup(f.read(), "html.parser")

    tag_infos = []
    for p in positions:
        tag = soup.find(id=p["placeholder"])
        if tag:
            content = tag.get_text(strip=True)
            html_snippet = str(tag)  # This will give you the full HTML for the tag
            tag_infos.append(
                {
                    "placeholder": p["placeholder"],
                    "original": content,
                    "length": len(content),
                    "html": html_snippet,  # Ensure the 'html' field is included
                }
            )

    # Step 3: Build final instruction for GPT to generate the replacement content
    final_instruction = (
        "Now that you've received the full account information, industry descriptions, persona details, concluded in the marketing pitch, "
        "make full use of this background knowledge, your task is to generate concise replacement content for each of "
        "the following HTML placeholders.\n"
        "The title should be attention-grabbing and relevant to the account.\n"
        "For all replacements, please ensure the content length is approximately similar to the original content length "
        "to preserve the visual layout of the landing page.\n"
        "The content should integrate the following critical details:\n"
        "  1. The **Account Name**: Mention the account name and tailor the content accordingly.\n"
        "  2. **Industry**: Address the specific challenges and characteristics of the account's industry.\n"
        "  3. **Persona**: Match the tone and content to the persona's role. This Account may have multiple personas, they have the demand ot the services (e.g., CFO, manager).\n"
        "  4. **Account's Services**: Highlight any services the account offers that are relevant to the context.\n"
        "  5. **Generated Content Length**: The content should be of approximately the same length as the original content to preserve the layout. And the logic of the content should be the same as the marketing pitch.\n"
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
        final_instruction += f"  Keep in mind you are a great marketing content generator, don't be a nerd, use in-depth marketing knowledge to generate the content.\n"
    # Step 4: Create the conversation for GPT (including the SystemMessage and HumanMessage)
    conversation = [
        SystemMessage(content="You are an expert in marketing content generation."),
        HumanMessage(
            content=f"Marketing Pitch for {account_info['name']}: {marketing_pitch}"
        ),
        HumanMessage(content=final_instruction),
    ]
    conversation_content = preview_conversation(conversation)
    log += "---------------Conversation Content-----------------\n"
    log += f"Conversation: {conversation_content}\n"
    log += "-----------------------------------------------------\n"
    # print(f"Conversation: {conversation}")

    # Step 5: Run the model
    
    attempt_count = 0
    # Step 6: Extract replacements from result
    replacements_dict = {}
    
    while attempt_count <= ATTEMPTS :
        print(f"Attempt {attempt_count + 1} of {ATTEMPTS}")
        result = llm.invoke(conversation)
        for line in result.content.splitlines():
            if line.startswith("REPLACEMENT for "):
                try:
                    key, value = line.split(":", 1)
                    key = key.replace("REPLACEMENT for", "").strip()
                    value = value.strip()
                    replacements_dict[key] = value
                except ValueError:
                    continue
        if validate_replacement_content(replacements_dict, account_info["name"]):
            print(f"Validation passed for attempt {attempt_count + 1}")
            break
        print(f"Validation failed for attempt {attempt_count + 1}")
        attempt_count += 1
    log += "---------------Replacements Dict-----------------\n"
    log += f"Replacements Dict: {replacements_dict}\n"
    log += "-----------------------------------------------------\n"
    # Save the replacements_dict to a json file for logging
    # with open("logs/replacements_dict.json", "w", encoding="utf-8") as f:
    #     json.dump(replacements_dict, f, ensure_ascii=False, indent=4)
    # Name the log for different Account
    # create the logs directory if it doesn't exist
    os.makedirs("logs", exist_ok=True)
    with open(
        f"logs/content_generation_log_{account_info['name']}.log", "w", encoding="utf-8"
    ) as f:
        f.write(log)
    return replacements_dict


def page_render(input_html_path, output_html_path, replacements):
    """
    Replaces specified content inside an HTML file and writes the result to a new file,
    preserving the original tag structure and nesting (e.g., <p>, <h1>, etc).
    """

    # Load and parse the HTML file
    with open(input_html_path, "r", encoding="utf-8") as file:
        soup = BeautifulSoup(file.read(), "html.parser")

    # Loop over each target ID and perform safe replacement
    for key, new_content in replacements.items():
        target = soup.find(id=key)

        if target:
            # Check if the target contains plain text
            if isinstance(target.string, NavigableString):
                # Simple case: just replace the string content
                target.string.replace_with(new_content)
            else:
                # More complex case (with nested tags): try to preserve structure
                try:
                    # Attempt to parse the new content as HTML to preserve nested structure
                    new_fragment = BeautifulSoup(new_content, "html.parser")

                    # Clear the target tag's existing content
                    target.clear()

                    # Append each element from the new fragment (preserving structure)
                    for el in new_fragment.contents:
                        target.append(el)
                except Exception as e:
                    print(
                        f"Warning: Could not parse replacement for {key}. Falling back to plain text."
                    )
                    target.string = new_content
        else:
            print(f"Warning: ID '{key}' not found in HTML. Skipped.")
    # create the output directory if it doesn't exist
    os.makedirs("output", exist_ok=True)
    # Write the updated HTML to output path
    with open(output_html_path, "w", encoding="utf-8") as file:
        file.write(str(soup))

    print(f"HTML customization completed. Output written to: {output_html_path}")
