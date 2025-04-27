from abc import ABC, abstractmethod
from typing import Any, Dict
from langchain.chat_models import ChatOpenAI
from langchain.schema import HumanMessage


class BaseGPTAgent(ABC):
    """
    Abstract base class for GPT agents using LangChain.
    """

    def __init__(self, model_name: str = "gpt-3.5-turbo", temperature: float = 0.7):
        self.llm = ChatOpenAI(model_name=model_name, temperature=temperature, request_timeout=60)

    @abstractmethod
    def build_prompt(self, input_data: Any) -> str:
        """
        Build the prompt string given the input data.
        """
        pass

    def run(self, input_data: Any) -> Dict[str, Any]:
        """
        Unified entry point for the agent: build prompt → call GPT → parse output.
        """
        prompt = self.build_prompt(input_data)
        response = self.llm.invoke([HumanMessage(content=prompt)])
        return self.parse_response(response.content, input_data)

    @abstractmethod
    def parse_response(self, raw_output: str, input_data: Any) -> Dict[str, Any]:
        """
        Parse the raw output from the LLM into a structured dict.
        """
        pass


