from typing import Any, Dict


def build_structured_reference_from_crawled_data(target_audience: str, crawled_data: Dict[str, Any]) -> str:
    data = crawled_data.get("data", {})
    purpose = data.get("main_purpose", "")
    products = data.get("key_products_or_services", "")
    audience = data.get("target_audience", "")
    slogans = data.get("notable_quotes_or_slogans", "")
    differentiators = data.get("competitive_differentiators", "")
    additional = data.get("additional_information", "")

    reference_parts = []
    if target_audience:
        reference_parts.append(f"• **Target Audience**: {target_audience}")
    if purpose:
        reference_parts.append(f"• **Purpose**: {purpose}")
    if products:
        reference_parts.append(f"• **Key Products/Services**: {products}")
    if audience:
        reference_parts.append(f"• **Target Audience**: {audience}")
    if slogans:
        reference_parts.append(f"• **Slogans**: {slogans}")
    if differentiators:
        reference_parts.append(f"• **Differentiators**: {differentiators}")
    if additional:
        reference_parts.append(f"• **Other Info**: {additional}")

    if not reference_parts:
        return "(No structured reference available from crawled content.)"

    return "**Structured Business Reference (from Target Audience website):**\n" + "\n".join(reference_parts)
