import time
import traceback
from typing import Optional

from src_.core.insight_agent import InsightAgent  # 请确保路径正确
from langchain_core.exceptions import LangChainException

async def crawl_content_from_url(
    url: str, 
    model_name: str = "gpt-4o", 
    temperature: float = 0.3,
    max_retry: int = 3,
    retry_delay: float = 1.0,  # seconds
    raw_html: Optional[str] = None,
    context: Optional[str] = None
) -> dict:
    """
    Use InsightAgent to deeply analyze and summarize the content of a URL or raw HTML.

    Args:
        url (str): The URL to analyze.
        raw_html (str, optional): Raw HTML content. If provided, the agent will skip live fetching.
        context (str, optional): Domain or use-case specific context for guiding summarization.
        model_name (str): LLM model to use (e.g., gpt-4o).
        temperature (float): LLM generation temperature.
        max_retry (int): Max retries on invalid output.
        retry_delay (float): Seconds to wait between retries.

    Returns:
        dict: {
            "success": bool,
            "url": str,
            "data": structured_insight,
            "error": str (optional)
        }
    """
    agent = InsightAgent(model_name=model_name, temperature=temperature)

    attempt = 0
    while attempt <= max_retry:
        try:
            inputs = {
                "url": url,
                "raw_html": raw_html,
            }
            if context:
                inputs["context"] = context

            result = agent.run(inputs)

            if result.get("success") and result.get("data"):
                return result

            attempt += 1
            if attempt > max_retry:
                print(f"[FAILED] Max retries reached for {url}. Returning last result.")
                return result

            print(f"[RETRY] InsightAgent returned invalid/empty result. Retrying ({attempt}/{max_retry})...")
            time.sleep(retry_delay)

        except LangChainException as lc_err:
            attempt += 1
            if attempt > max_retry:
                print(f"[FAILED] LangChain error max retries exceeded for {url}. Error: {lc_err}")
                return {
                    "success": False,
                    "url": url,
                    "data": None,
                    "error": str(lc_err)
                }
            print(f"[RETRY] LangChain error ({attempt}/{max_retry}): {lc_err}")
            time.sleep(retry_delay)

        except Exception as e:
            print(f"[Unexpected Error] {traceback.format_exc()}")
            raise RuntimeError(f"Unexpected error during InsightAgent crawling for {url}: {str(e)}") from e
