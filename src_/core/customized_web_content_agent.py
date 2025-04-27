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
            raise ValueError("positions, marketing_pitch, and target_audience must be provided.")

        sections_text = "\n".join(
            f"- {list(section.keys())[0]}: {list(section.values())[0]}" for section in positions
        )

        if structured_info:
            structured_info_text = "\n".join(
                f"- {key}: {value}" for key, value in structured_info.items() if value
            )
            structured_block = f"""
Additional structured business information to guide you:

---
{structured_info_text}
---
"""
        else:
            structured_block = ""

        prompt = f"""
You are a professional website copywriter specialized in SaaS and service-based industries.

Below is the new **Marketing Pitch** you should embody in all rewritten content:

---
{marketing_pitch}
---

{structured_block}

Here are the **current website sections**, in order:

---
{sections_text}
---

**Task Instructions:**
- Rewrite each section individually.
- Each rewritten section must:
    - Naturally and clearly mention the target audience: **\"{target_audience}\"** several times.
    - Focus on the target audience's needs and challenges, not just promoting the company itself.
    - Match the company's services to the target audience's needs.
    - Reflect the tone, themes, and messaging from the Marketing Pitch.
    - Respect the original section's role and approximate length (±10%), this is a requirement, make sure generate content is strictly aligned with the original section's role and length.
    - Maintain logical flow and consistency across sections.
    - Use concise, theme-highlighted style for headings (h1, h2) and richer informative style for paragraphs (p, li).
    - Keep the original tag_id as the output key.

**Strict Output Format:**
```json
{{
    "tag_id_1": "rewritten content for section 1",
    "tag_id_2": "rewritten content for section 2",
    ...
}}
```

**Important:**
- Output only the JSON object, no extra text, no comments.
- Maintain the input tag order.
- Craft persuasive, customer-centric, polished B2B marketing website content aligned with the pitch.
        """
        return prompt.strip()

    def parse_response(self, raw_output: str, input_data: Dict[str, Any]) -> Dict[str, Any]:
        try:
            parsed = json.loads(raw_output)
            if not isinstance(parsed, dict):
                raise ValueError("Parsed output is not a dictionary.")
            return {"success": True, "rewritten_content": parsed}
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to parse JSON: {str(e)}",
                "raw_output": raw_output
            }
