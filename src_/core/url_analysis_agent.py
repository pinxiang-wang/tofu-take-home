
from typing import Any, Dict
from src_.core.base_agent import BaseGPTAgent


class URLAnalysisAgent(BaseGPTAgent):
    """
    An agent to analyze and summarize the content of a webpage URL.
    """

    def build_prompt(self, input_data: Dict[str, str]) -> str:
        url = input_data.get("url", "")
        raw_html = input_data.get("raw_html", "")
        context = input_data.get("context", "")

        prompt = f"""
            You are a professional webpage content analyst.

            Given the following webpage:

            URL: {url}
            HTML Content (truncated to 3000 chars): {raw_html[:3000]}
            Context: {context}

            Please extract the following in JSON format:
            - Main purpose of the website
            - Key products or services
            - Target audience
            - Notable quotes or slogans
            - Competitive differentiators
            - Any other relevant information or a summary of the website

            Respond ONLY with a JSON object.
            """
        return prompt

    def parse_response(
        self, raw_output: str, input_data: Dict[str, str]
    ) -> Dict[str, Any]:
        # Simple parsing: Assume the model already returns a JSON-looking string
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