import json
import time
from typing import Dict, List, Optional, Any
from src_.core.base_agent import BaseGPTAgent  # 替换成你的实际导入路径
from langchain_core.exceptions import LangChainException
import requests
import socket
import urllib3


class CustomizedWebContentAgent(BaseGPTAgent):
    """
    An agent that customizes and rewrites webpage sections based on a marketing pitch,
    and optionally structured info, while preserving structure, order, and length.
    """

    def build_prompt(self, input_data: Dict[str, Any]) -> str:
        positions = input_data.get("positions", [])
        marketing_pitch = input_data.get("marketing_pitch", "")
        target_audience = input_data.get("target_audience", "")
        structured_info = input_data.get("structured_info", {})

        if not positions or not marketing_pitch or not target_audience:
            raise ValueError(
                "positions, marketing_pitch, and target_audience must be provided."
            )

        sections_text = "\n".join(
            f"- Tag: {list(section.keys())[0]}  "
            f"(This is a unique tag identifier, indicating both the HTML tag type and its position in the page. "
            f"Example: 'h1-1' means the first <h1> heading, 'p-2' means the second paragraph.)\n"
            f"  Content (length {len(list(section.values())[0])} chars): {list(section.values())[0]}"
            for section in positions
        )

        structured_info_text = "\n".join(
            f"- {key}: {value}" for key, value in structured_info.items() if value
        )
        prompt = f"""
            You are a professional website copywriter specialized in SaaS and service-based industries.

            Below is the new **Marketing Pitch** you should embody in all rewritten content:

            ---
            {marketing_pitch}
            ---

            Learn the original length of each section first and make generated content strictly align with each section's length.
            **Task Instructions:**
            - Rewrite each section individually.
            - Each rewritten section must:
                - Naturally and clearly mention the target audience: **\"{target_audience}\"** several times.
                - Don't mention the company name in the rewritten content, instead, use the service provided by the company to match the target audience's needs.
                - Match the company's services to the target audience's needs.
                - Reflect the tone, themes, and messaging from the Marketing Pitch.
                - Respect the original section's role and approximate length (±10%), this is a requirement,
                - Maintain logical flow and consistency across sections.
                - Use concise, theme-highlighted style for headings (h1, h2) and richer informative style for paragraphs (p, li).
                - Keep the original tag_id as the output key.


                Output format strictly as valid JSON:
                ```json
                {{
                    "tag_id_1": "rewritten content for section 1",
                    "tag_id_2": "rewritten content for section 2",
                    ...(upon the number of sections)
                }}

                **Important:**
                - Output only the JSON object, no extra text, no comments.
                - Calculate the each  original length first and strictly align with the length.
                - Maintain the input tag order.
                - Strictly follow the length of the original content.
        Below is the tag-content pairs section that you should rewrite:
        """
        prompt += sections_text
        return prompt.strip()

    def parse_response(
        self, raw_output: str, input_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        try:
            parsed = json.loads(raw_output)
            if not isinstance(parsed, dict):
                raise ValueError("Parsed output is not a dictionary.")
            return {"success": True, "rewritten_content": parsed}
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to parse JSON: {str(e)}",
                "raw_output": raw_output,
            }
