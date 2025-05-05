from src_.core.customized_web_content_agent import CustomizedWebContentAgent
import time
from typing import List, Dict

from typing import List, Dict
from bs4 import BeautifulSoup


def extract_tagged_content_from_html(
    positions: List[Dict[str, str]], html_file_path: str
) -> List[Dict[str, str]]:
    """
    Extract HTML content blocks based on placeholder IDs from a local HTML file.

    Args:
        positions (List[Dict[str, str]]): List of {"placeholder": id_string}.
        html_file_path (str): Path to the HTML file.

    Returns:
        List[Dict[str, str]]: Each dict maps {tag_id: HTML snippet (including original tag)}.
    """
    with open(html_file_path, "r", encoding="utf-8") as f:
        html_content = f.read()

    soup = BeautifulSoup(html_content, "html.parser")
    extracted_positions = []

    for position in positions:
        placeholder_id = position.get("placeholder")
        if not placeholder_id:
            continue

        element = soup.find(id=placeholder_id)
        if element:
            tag_id = placeholder_id
            full_tag_html = str(element)
            extracted_positions.append({tag_id: full_tag_html})
        else:
            print(f"[WARN] ID '{placeholder_id}' not found in HTML. Skipping.")

    return extracted_positions


def generate_customized_web_content(
    target_audience: str,
    positions: List[Dict[str, str]],
    marketing_pitch: str,
    model_name: str = "gpt-3.5-turbo",
    temperature: float = 0.3,
    max_retries: int = 3,
    retry_delay: float = 3,
) -> Dict[str, str]:
    """
    Use CustomizedWebContentAgent to generate rewritten webpage content for each tag + html snippet.

    Args:
        positions (List[Dict[str, str]]): List of {tag_id: original_html_fragment}.
        marketing_pitch (str): The new marketing pitch text.
        model_name (str): Model to use.
        temperature (float): Temperature for generation.
        max_retries (int): Maximum retries on API errors.
        retry_delay (float): Delay between retries in seconds.

    Returns:
        Dict[str, str]: Mapping {tag_id: rewritten_html_fragment}.
    """
    agent = CustomizedWebContentAgent(model_name=model_name, temperature=temperature)

    input_data = {
        "target_audience": target_audience,
        "positions": positions,
        "marketing_pitch": marketing_pitch,
    }

    attempt = 0
    while attempt <= max_retries:
        try:
            result = agent.run(input_data)
            if result.get("success"):
                return result["rewritten_content"]
            else:
                raise RuntimeError(f"Agent failed: {result.get('error')}")

        except Exception as e:
            attempt += 1
            if attempt > max_retries:
                raise RuntimeError(
                    f"Customized web content generation failed after {max_retries} retries: {str(e)}"
                ) from e
            print(
                f"[RETRY] Error on attempt {attempt}/{max_retries}: {e}. Retrying after {retry_delay} seconds..."
            )
            time.sleep(retry_delay)
