from src_.core.marketing_pitch_generation_agent import MarketingPitchGenerationAgent
from langchain_core.exceptions import LangChainException
import time
import traceback
import requests
import socket
import urllib3

def generate_marketing_pitch(
    text: str, 
    crawled_content: dict, 
    company_info: str,    
    model_name: str = "gpt-3.5-turbo", 
    temperature: float = 0.4,
    max_retries: int = 3,
    retry_delay: float = 1.5
) -> str:
    """
    Generate a marketing pitch based on account text, structured crawled content, and company's own description,
    with full retry mechanism for connection errors.
    """
    # if not text:
    #     raise ValueError("Account text must be provided.")
    
    # if not isinstance(crawled_content, dict):
    #     raise ValueError("Crawled content must be a dictionary.")

    # if not company_info:
    #     raise ValueError("Company description must be provided.")

    
    print(f"[DEBUG] text: {text}")
    print(f"[DEBUG] crawled_content: {crawled_content}")
    print(f"[DEBUG] company_info: {company_info}")
    
    input_data = {
        "text": text,
        "crawled_content": crawled_content,
        "company_info": company_info  
    }

    agent = MarketingPitchGenerationAgent(model_name=model_name, temperature=temperature)

    attempt = 0
    while attempt <= max_retries:
        try:
            result = agent.run(input_data)

            if result.get('success'):
                return result['marketing_pitch']
            else:
                raise RuntimeError(f"Failed to generate marketing pitch: {result.get('error')}")

        except (
            LangChainException,
            requests.exceptions.RequestException,
            urllib3.exceptions.HTTPError,
            socket.error
        ) as conn_err:
            attempt += 1
            if attempt > max_retries:
                print(f"[FAILED] Max retries exceeded. Last error: {conn_err}")
                raise RuntimeError(f"LLM invocation failed after {max_retries} retries: {str(conn_err)}") from conn_err

            print(f"[RETRY] Connection-related error on attempt {attempt}/{max_retries}: {conn_err}. Retrying after {retry_delay} seconds...")
            time.sleep(retry_delay)

        except Exception as e:
            print(f"[Unexpected Error] {traceback.format_exc()}")
            raise RuntimeError(f"Unexpected error during marketing pitch generation: {str(e)}") from e
