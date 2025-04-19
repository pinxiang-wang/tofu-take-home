# write a test for the generate_landing_page function
from src.marketing_content_gen import generate_landing_page
from src.playbook_knowledge_gen import load_playbook_data, categorize_playbook_data

# Load playbook data
playbook_data = load_playbook_data('playbook_data.json')
categorized_playbook_data = categorize_playbook_data(playbook_data)

def test_generate_landing_page():
    # Get the account info from the categorized playbook data
    account_info = categorized_playbook_data['accounts'][0]
    industry_descriptions = categorized_playbook_data['industries']
    persona_descriptions = categorized_playbook_data['personas']
    # print(f"Account Info: {account_info}")
    # print(f"Industry Descriptions: {industry_descriptions}")
    # print(f"Persona Descriptions: {persona_descriptions}")  
    # Generate the landing page content
    landing_page_content = generate_landing_page(account_info, industry_descriptions, persona_descriptions)
    
    # Save the generated content to a log file
    with open("logs/landing_page_output.log", "w") as f:
        f.write(landing_page_content)

test_generate_landing_page()
