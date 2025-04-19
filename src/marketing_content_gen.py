import openai
from bs4 import BeautifulSoup
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain
from langchain_openai import ChatOpenAI
from langchain.schema import HumanMessage, SystemMessage
from langchain.text_splitter import RecursiveCharacterTextSplitter


# Initialize the GPT model
llm = ChatOpenAI(temperature=0.7, model="gpt-3.5-turbo")


# Function to fetch and summarize URL content using LangChain
def parse_account_url_with_langchain(account_url: str, max_length=1500) -> str:
    try:
        # Create a prompt template for LangChain
        prompt_template = f"""
        Given the URL: {account_url}, summarize the content of the webpage into a short description. 
        Focus on key information about the company, its products, and services, no longer than {max_length} characters.
        """

        # Initialize the LLM (OpenAI in this case) with LangChain
        llm = ChatOpenAI(temperature=0.7, model="gpt-3.5-turbo")

        # Create the LangChain with the prompt template
        prompt = PromptTemplate(input_variables=["account_url"], template=prompt_template)
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
def chunk_text(text, max_tokens=1500):
    splitter = RecursiveCharacterTextSplitter(chunk_size=max_tokens, chunk_overlap=100)
    return splitter.split_text(text)


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
def generate_landing_page(account_info, industry_descriptions, persona_descriptions):
    account_name = account_info['name']
    account_url = account_info['context']
    
    # Step 1: Extract and chunk the account knowledge
    account_knowledge = parse_account_url_with_langchain(account_url)  # Assumes HTML parsed cleanly
    account_chunks = chunk_text(account_knowledge)

    # Step 2: Chunk industry and persona descriptions
    industry_chunks = chunk_text(" ".join([d["context"] for d in industry_descriptions]))
    persona_chunks = chunk_text(" ".join([d["context"] for d in persona_descriptions]))

    # Step 3: Initialize conversation
    conversation = [
        SystemMessage(content="You are an expert in marketing content generation."),
        HumanMessage(content=(
            "I will provide the account background and relevant persona/industry descriptions in several parts.\n"
            "Please wait until I indicate that all parts have been submitted before replying.\n"
            "Respond only after receiving the final instruction."
        )),
        HumanMessage(content=f"Account Name: {account_name}"),
        HumanMessage(content=f"Account URL: {account_url}")
    ]

    # Step 4: Add account knowledge
    for idx, chunk in enumerate(account_chunks):
        conversation.append(HumanMessage(content=f"[Account Description - Part {idx+1}]:\n{chunk}"))

    # Step 5: Add industry description
    for idx, chunk in enumerate(industry_chunks):
        conversation.append(HumanMessage(content=f"[Industry Descriptions - Part {idx+1}]:\n{chunk}"))

    # Step 6: Add persona description
    for idx, chunk in enumerate(persona_chunks):
        conversation.append(HumanMessage(content=f"[Persona Descriptions - Part {idx+1}]:\n{chunk}"))

    # Step 7: Final instruction
    final_instruction = (
        "Now that you've received the full account information and descriptions,\n"
        "please classify this account into the most relevant Industry and Persona.\n"
        "Use the knowledge of our description of targeted industries and personas to make the best match.\n"
        "Then, generate a customized and compelling marketing pitch for this account, "
        "tailored to the account's needs and preferences, "
        "and make sure the tone is appropriate for the account's persona and industry.\n"
        "This content is displayed on a landing page, so it should be concise and engaging\n"
        "Don't sound like a salesperson, but rather like a trusted advisor."
        
    )

    # validate the content of the conversation sent to model:
    print(f"Conversation: {conversation}")


    conversation.append(HumanMessage(content=final_instruction))
    preview_conversation(conversation)

    # Step 8: Run the chat model
    result = llm.invoke(conversation)

    return result.content

def preview_conversation(conversation, output_path="logs/conversation_preview.log"):
    """
    Join all conversation messages into one readable string for inspection.
    Saves the full prompt content into a log file for verification.
    """
    preview_text = ""
    for message in conversation:
        role = message.type if hasattr(message, 'type') else message.__class__.__name__
        content = message.content
        preview_text += f"\n--- {role.upper()} ---\n{content}\n"

    # Write to file
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(preview_text)

    print(f"[Preview Saved] Full conversation written to {output_path}")