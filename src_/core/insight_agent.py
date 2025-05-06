from typing import Any, Dict
from src_.core.base_agent import BaseGPTAgent


class InsightAgent(BaseGPTAgent):
    """
    A more detailed and structured agent to analyze a webpage's raw HTML and return
    expanded insight into business domain, services, audience, etc.
    """

    def build_prompt(self, input_data: Dict[str, str]) -> str:
        url = input_data.get("url", "")
        raw_html = input_data.get("raw_html", "")
        context = input_data.get("context", "")
        print(f"[DEBUG] raw_html: {raw_html}")
        prompt = f"""
        You are a senior business analyst with expertise in web content understanding.

        Your task is to analyze the following webpage and provide a highly detailed summary, 
        with **each section written in no less than 200 words**:

        URL: {url}

        HTML Content (truncated to 3000 characters):
        {raw_html[:3]}

        Business Context (optional, may help guide your focus): {context}

        Based on the above, extract and return the following fields in a **raw JSON object**:
        {{
            "main_business": "...",                 # A thorough explanation of the business's primary domain and goals.
            "key_services_or_products": "...",      # Describe in detail what services/products they provide.
            "industry": "...",                      # Identify the business's industry or sub-industry with reasoning.
            "target_audience": "...",               # Analyze the primary audience(s) and their needs.
            "value_proposition": "...",             # What differentiates this organization from others?
            "summary": "..."                        # A full coherent overview as if explaining the business to a stakeholder.
        }}

        Your response MUST meet the following criteria:
        - Each field should be a complete, natural-language paragraph with a minimum of 200 words.
        - The JSON object must be valid and NOT wrapped in markdown or explanations.
        - DO NOT include any extra commentary or text before/after the JSON.
        - Output ONLY the raw JSON string.
        """
        return prompt

    def parse_response(
        self, raw_output: str, input_data: Dict[str, str]
    ) -> Dict[str, Any]:
        import json
        try:
            parsed = json.loads(raw_output)
            return {"success": True, "url": input_data.get("url"), "data": parsed}
        except Exception as e:
            return {
                "success": False,
                "url": input_data.get("url"),
                "error": str(e),
                "raw_output": raw_output,
            }
