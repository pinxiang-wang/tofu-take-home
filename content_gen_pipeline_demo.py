from src.marketing_content_gen import (
    page_render,
    replacement_content_gen_with_pitch,
)
import os
from src.playbook_parser import PlaybookParser
from src.playbook_knowledge_gen import load_playbook_data, categorize_playbook_data


if __name__ == "__main__":

    # parse the company and target info into a json file
    company_info_path = "data/company_info.json"
    target_info_path = "data/target_info.json"

    parser = PlaybookParser(company_info_path, target_info_path)

    output_path = "output/playbook_data.json"
    # create the output directory if it doesn't exist
    os.makedirs("output", exist_ok=True)
    parser.save_to_json(output_path)
    # load the playbook data
    playbook_data = load_playbook_data(output_path)
    # categorize the playbook data
    categorized_playbook_data = categorize_playbook_data(playbook_data)

    # generate the landing page
    # Loop over all accounts in the categorized playbook data
    for account in categorized_playbook_data["accounts"]:
        account_name = account["name"]
        account_info = account
        industry_descriptions = categorized_playbook_data["industries"]
        persona_descriptions = categorized_playbook_data["personas"]

        # Define the positions (placeholders) in the HTML template
        positions = [
            {
                "placeholder": "hs_cos_wrapper_widget_1611686344563"  # Main headline text
            },
            {
                "placeholder": "hs_cos_wrapper_banner"  # Paragraph describing the economic context and actions
            },
            {
                "placeholder": "hs_cos_wrapper_widget_1609866779313"  # Subtitle just below the headline
            },
        ]

        # Generate the replacement content for the current account's landing page
        result_dict = replacement_content_gen_with_pitch(
            account_info,
            industry_descriptions,
            persona_descriptions,
            positions,
            "data/landing_page.html",
        )

        # Use the account name to create a unique output file
        output_html_path = f"output/{account_name}_landing_page.html"

        # Generate and save the landing page
        page_render("data/landing_page.html", output_html_path, result_dict)
        print(
            f"Landing page generated for account: {account_name} and saved to {output_html_path}"
        )
