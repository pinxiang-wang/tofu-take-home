from typing import Dict

from src_.core.base_agent import BaseGPTAgent

class MarketingPitchGenerationAgent(BaseGPTAgent):
    """
    Agent to generate a marketing pitch based on company's provided text and partial crawled content,
    gracefully handling missing or incomplete structured data.
    """

    def build_prompt(self, input_data: Dict[str, any]) -> str:
        """
        Build a marketing pitch prompt using plain text aggregation from company description and website crawl.
        """
        company_text = input_data.get("text", "")
        crawled_data = input_data.get("crawled_content", {})
        company_info = input_data.get("company_info", {})
        
        print(f"[DEBUG] company_text: {company_text}")
        print(f"[DEBUG] crawled_data: {crawled_data}")
        print(f"[DEBUG] company_info: {company_info}")

        # 把所有可用内容拼成一段 "参考资料"
        references = []

        if company_text:
            references.append(f"Company’s business description towards the target audience:\n{company_text}")

        if company_info:
            references.append(f"Company’s own description:\n{company_info}")

        if crawled_data:
            references.append(f"Target audience's description, key products/services, competitive differentiators, and website summary:\n{crawled_data}")

        # 最后整体作为大文本
        background_info = "\n\n".join(references)

        prompt = f"""
            You are a professional marketing strategist specializing in B2B SaaS and service industries.

            Below is detailed background information about a company from multiple sources:

            {background_info}

            Your task:
            - Review all the provided information holistically.
            - The target audience can be a specific company, specific industry, or specific role.
            - Mention the belong of the target audience. e.g. "The target audience is the CEO of a manufacturing company in China.", "YMCA is a non-profit organization that provides services to the community which need XXX for building a better community."
            - No need to mention the title of the company deliberately. Instead, conclude the company's business description and service towards the target audience.
            - Make sure the targeted audience is the main focus of the pitch. And mention the audience's pain points and needs.
            - Illustrate the necessary reasons for the audience to use the product/service.
            - Organize the pitch with a logical structure.
        

            Tone: Professional, insightful, business-driven.  
            Length: Around 450–550 words.  
            Output: Only the final marketing pitch. No explanations, no headings, no bullet points.

            Emphasize clear storytelling, value propositions, and emotional connection with decision-makers.
                """.strip()

        return prompt


    def parse_response(self, raw_output: str, input_data: Dict[str, str]) -> Dict[str, any]:
        return {"success": True, "marketing_pitch": raw_output.strip()}
