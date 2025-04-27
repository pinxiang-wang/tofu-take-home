import time
from src_.core.url_analysis_agent import URLAnalysisAgent
from langchain_core.exceptions import LangChainException
import traceback

def crawl_content_from_url(
    url: str, 
    model_name: str = "gpt-4", 
    temperature: float = 0.3,
    max_retry: int = 3,
    retry_delay: float = 1.0  # seconds
) -> dict:
    """
    Use URLAnalysisAgent to crawl and summarize a URL content, with retry mechanism and exception handling.

    Args:
        url (str): The URL to analyze.
        raw_html (str): (Optional) The raw HTML content if already fetched.
        context (str): (Optional) The context or domain info to guide the summarization.
        model_name (str): Model name to use (default: gpt-4).
        temperature (float): Sampling temperature (default: 0.3).
        max_retry (int): Maximum number of retries if invalid response detected.
        retry_delay (float): Delay between retries (in seconds).

    Returns:
        dict: Structured output from the Agent, including success flag, data, etc.
    """
    agent = URLAnalysisAgent(model_name=model_name, temperature=temperature)
    
    attempt = 0
    while attempt <= max_retry:
        try:
            result = agent.run({
                "url": url,
            })

            # Result template:
            # {
            #     "success": True,
            #     "url": url,
            #     "data": data
            # }
            
            if result.get("success") and result.get("data") != "Unable to determine from the provided information":
                return result
            else:
                attempt += 1
                if attempt > max_retry:
                    print(f"[FAILED] Max retries reached for {url}. Returning last result.")
                    return result
                print(f"[RETRY] Received 'Unable to determine' for {url}. Retrying (attempt {attempt}/{max_retry})...")
                time.sleep(retry_delay)

        except LangChainException as lc_err:
            attempt += 1
            if attempt > max_retry:
                print(f"[FAILED] Max retries reached due to LangChain error for {url}. Last error: {lc_err}")
                return {
                    "success": False,
                    "url": url,
                    "data": None,
                    "error": str(lc_err)
                }
            print(f"[RETRY] LangChain error on attempt {attempt}/{max_retry} for {url}: {lc_err}. Retrying after {retry_delay} seconds...")
            time.sleep(retry_delay)

        except Exception as e:
            print(f"[Unexpected Error] {traceback.format_exc()}")
            raise RuntimeError(f"Unexpected error during URL content crawling for {url}: {str(e)}") from e
