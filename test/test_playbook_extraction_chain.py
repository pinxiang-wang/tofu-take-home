import os
from src.playbook_extraction_chain import create_company_chain, create_target_chain
from langchain_openai import ChatOpenAI

# Example usage
if __name__ == "__main__":
    import json

    # Load your JSON files as strings
    with open("data/company_info.json", "r") as f:
        company_info_json = f.read()

    with open("data/target_info.json", "r") as f:
        target_info_json = f.read()

    # import os

    llm = ChatOpenAI(
        temperature=0.2, model_name="gpt-4o", openai_api_key=os.getenv("OPENAI_API_KEY")
    )

    # Run company info chain
    company_chain = create_company_chain(llm)
    company_summary = company_chain.run(json_input=company_info_json)

    with open("output/company_info_summary.txt", "w") as f:
        f.write(company_summary)

    # Run target info chain
    target_chain = create_target_chain(llm)
    target_summary = target_chain.run(json_input=target_info_json)

    with open("output/target_info_summary.txt", "w") as f:
        f.write(target_summary)

    print("Extraction completed. Summaries written to disk.")
