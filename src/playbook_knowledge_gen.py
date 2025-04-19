import json
import requests
from bs4 import BeautifulSoup
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
from typing import Dict
import re

# Initialize the SentenceTransformer model for sentence embeddings
model = SentenceTransformer('paraphrase-MiniLM-L6-v2')

# Load data from the JSON file
def load_playbook_data(file_path: str):
    with open(file_path, 'r', encoding='utf-8') as f:
        return json.load(f)
# Function to remove unwanted content such as phone numbers, addresses, and license numbers
def remove_contact_info(text: str) -> str:
    # Remove phone numbers (patterns like (123) 456-7890 or 123-456-7890)
    phone_pattern = r'\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}'
    text = re.sub(phone_pattern, '', text)

    # Remove email addresses (simple pattern for email)
    email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b'
    text = re.sub(email_pattern, '', text)

    # Remove addresses (a simple pattern matching common address formats)
    address_pattern = r'\d{1,5}\s\w+(\s\w+)+,\s\w{2}\s\d{5}'
    text = re.sub(address_pattern, '', text)

    # Remove license numbers (patterns like 'License: ABC123' or 'Lic. # ABC123')
    license_pattern = r'(License|Lic\.)\s*[:#]?\s*[A-Za-z0-9]+'
    text = re.sub(license_pattern, '', text)

    return text

# Define the method to parse the account URL and extract relevant description content
def parse_account_url(account_url: str) -> str:
    try:
        # Fetch the content from the account's URL
        response = requests.get(account_url)
        response.raise_for_status()  # Check if the request was successful
        
        # Parse the content using BeautifulSoup
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Extract textual content from the page
        paragraphs = soup.find_all('p')  # Find all paragraph tags
        descriptions = " ".join([para.get_text().strip() for para in paragraphs if para.get_text().strip()])
        
        # You can also extract other tags like h1, h2, etc., if needed
        headings = soup.find_all(['h1', 'h2', 'h3'])  # Find all heading tags
        headings_text = " ".join([heading.get_text().strip() for heading in headings])
        
        # Combine headings and descriptions to form the account knowledge
        account_knowledge = headings_text + "\n" + descriptions
        
        # Remove unwanted content (phone numbers, addresses, and license numbers)
        account_knowledge = remove_contact_info(account_knowledge)
        
        return account_knowledge
    
    except requests.exceptions.RequestException as e:
        print(f"Error fetching the URL: {e}")
        return ""


def get_embeddings(texts):
    """Generate embeddings for a list of texts."""
    return model.encode(texts)

def calculate_similarity(account_description, industry_descriptions, persona_descriptions):
    """
    Calculate the cosine similarity between the account description and each industry/persona description.
    Returns the most similar industry and persona.
    """
    # Get embeddings for the account description, industries, and personas
    all_descriptions = industry_descriptions + persona_descriptions
    embeddings = get_embeddings([account_description] + all_descriptions)
    
    account_embedding = embeddings[0]
    industry_embeddings = embeddings[1:1+len(industry_descriptions)]
    persona_embeddings = embeddings[1+len(industry_descriptions):]
    
    # Calculate cosine similarities
    industry_similarities = cosine_similarity([account_embedding], industry_embeddings)[0]
    persona_similarities = cosine_similarity([account_embedding], persona_embeddings)[0]
    
    # Get the most similar industry and persona
    most_similar_industry_idx = industry_similarities.argmax()
    most_similar_persona_idx = persona_similarities.argmax()

    # Return the best matching industry and persona
    most_similar_industry = industry_descriptions[most_similar_industry_idx]
    most_similar_persona = persona_descriptions[most_similar_persona_idx]

    return most_similar_industry, most_similar_persona

# Define a method to process the target and extract account knowledge
def process_account_target(target: Dict[str, str]):
    if target['target_type'] == 'Accounts':
        account_url = target.get('context', '')  # Assuming the URL is stored in 'context'
        if account_url:
            print(f"Extracting knowledge for account: {target['name']} from {account_url}")
            account_knowledge = parse_account_url(account_url)
            print(f"Account Knowledge for {target['name']}:\n{account_knowledge}")
        else:
            print(f"No URL found for account: {target['name']}")



def categorize_playbook_data(playbook_data):
    company_info = playbook_data.get("company_info", {})
    targets = playbook_data.get("targets", [])

    categorized_data = {
        "company_info": company_info,
        "accounts": [],
        "personas": [],
        "industries": []
    }

    # Categorize targets based on their type
    for target in targets:
        target_type = target.get("target_type", "Unknown")
        name = target.get("name", "Unnamed")
        context = target.get("context", "")

        if target_type == "Accounts":
            categorized_data["accounts"].append({"name": name, "context": context})
        elif target_type == "Personas":
            categorized_data["personas"].append({"name": name, "context": context})
        elif target_type == "Industries":
            categorized_data["industries"].append({"name": name, "context": context})

    return categorized_data



def process_playbook_data(playbook_data, log_file_path='account_descriptions.log'):
    company_info = playbook_data.get("company_info", {})
    targets = playbook_data.get("targets", [])

    persona_descriptions = []  # List to store persona descriptions
    industry_descriptions = []  # List to store industry descriptions

    # Extract persona and industry descriptions from target data
    for target in targets:
        target_type = target.get("target_type", "Unknown")
        name = target.get("name", "Unnamed")
        context = target.get("context", "")

        # Process Personas and Industries
        if target_type == "Personas":
            description = target.get("context", "")
            if description:
                persona_descriptions.append({"name": name, "description": description})
        
        elif target_type == "Industries":
            description = target.get("context", "")
            if description:
                industry_descriptions.append({"name": name, "description": description})

    # Process company_info (can simply output each field)
    for field, value in company_info.items():
        print(f"{field}: {value}")

    # List to store account knowledge and associated descriptions
    account_knowledge_list = []

    # Process targets (output by category)
    for target in targets:
        target_type = target.get("target_type", "Unknown")
        name = target.get("name", "Unnamed")
        context = target.get("context", "")

        # Assuming 'account_name' is the name of the account you are processing
        if target_type == "Accounts":
            if context:  # Ensure there's a URL
                print(f"Extracting knowledge for account: {name} from {context}")
                
                # Get the knowledge from the account URL
                account_knowledge = parse_account_url(context)  # Assuming this function extracts knowledge from the URL
                
                # Include the account name in the content to calculate similarity
                account_knowledge_with_name = f"Account: {name}\n Description: {account_knowledge}"
                
                # Calculate similarity to personas and industries
                most_similar_industry, most_similar_persona = calculate_similarity(
                    account_knowledge_with_name,  # Use the name-inclusive account knowledge
                    [industry["description"] for industry in industry_descriptions], 
                    [persona["description"] for persona in persona_descriptions]
                )

                # Log the results for this account, including the industry and persona information
                with open(log_file_path, 'a', encoding='utf-8') as log_file:
                    log_file.write(f"Account: {name}\n")
                    log_file.write(f"URL: {context}\n")
                    log_file.write(f"Description:\n{account_knowledge}\n")
                    log_file.write(f"Most Similar Personas: {most_similar_persona}\n")
                    log_file.write(f"Most Similar Industries: {most_similar_industry}\n")
                    log_file.write("\n" + "-"*50 + "\n")  # Separator for clarity

                print(f"Account Knowledge for {name} has been written to the log file.")
                
                # Append the result to the list of account knowledge
                account_knowledge_list.append({
                    "account_name": name,
                    "account_knowledge": account_knowledge_with_name,
                    "most_similar_industry": most_similar_industry,
                    "most_similar_persona": most_similar_persona
                })
            else:
                print(f"No URL found for account: {name}")
    # Return the list of account knowledge, which can be used for content generation
    return account_knowledge_list

