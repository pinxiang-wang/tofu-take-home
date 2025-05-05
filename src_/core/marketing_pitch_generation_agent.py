from typing import Dict

from src_.core.base_agent import BaseGPTAgent
from src_.utils.prompt_utils import build_structured_reference_from_crawled_data

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
        target_audience = input_data.get("target_audience", "")
        
        # print(f"[DEBUG] company_text: {company_text}")
        # print(f"[DEBUG] crawled_data: {crawled_data}")
        # print(f"[DEBUG] company_info: {company_info}")
        print(f"[DEBUG] target_audience: {target_audience}")

        references = []

        if company_text:
            references.append(f"Company’s business description towards the target audience:\n{company_text}")

        if company_info:
            references.append(f"Company’s own description:\n{company_info}")

        if crawled_data and crawled_data.get("success"):
            structured_reference = build_structured_reference_from_crawled_data(target_audience, crawled_data)
            references.append(structured_reference)
        background_info = "\n\n".join(references)

        prompt = f"""
            You are a professional marketing strategist specializing in B2B SaaS and service industries.

            Below is detailed background information about a target audience from multiple sources:
            
            Make it clear about the difference between the target audience and the company.
            
            **Important Instructions**
            - The target audience is the main topic of this pitch. It's the marketing target of the company.
            - The target audience can be a specific company, specific industry, or specific role.
            - The company is the provider of the product/service.
            - Base on the description of the business of the company, analysis the target audience's pain points and needs.
            - Try to organized the content with: The company's product/service is the solution to the target audience's pain points and needs.
            - Do not mention the company's name deliberately. Instead, conclude the company's business description and service towards the target audience.
            
            {background_info}
            
            *Target Audience* {target_audience},
            
            The target audience serves as the main subject of the entire marketing pitch and forms the narrative focus.
            The logic is to analyze the needs of the target audience within their specific industry in today’s context, and then illustrate how the services—provided by the company—fulfill those needs.   

            Your task:
            - Review all the provided information holistically.
            - Identified the target audience entity and the company entity from the background information.
            - Identified the target audience's type e.g. "The target audience is the CEO of a manufacturing company in China.", "YMCA is a non-profit organization that provides services to the community which need XXX for building a better community."
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
