from langchain_ollama import ChatOllama
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from pydantic import BaseModel
from typing import Literal
from prompts import CORRECTNESS_PROMPT, GROUNDEDNESS_PROMPT
from os import getenv


class EvaluationResult(BaseModel):
    analysis: str
    verdict: Literal["good", "satisfactory", "unsatisfactory"]


class Judge:
    def __init__(
        self,
        model="qwen3:8b",
        base_url=getenv("OLLAMA_URL"),
        temperature=0.0,
        **kwargs
    ):
        self.model_name = model
        self.base_url = base_url
        self.temperature = temperature

        self.llm = ChatOllama(
            model=model,
            base_url=base_url,
            temperature=temperature,
            reasoning=True,
            **kwargs
        )

        # JSON output parser for parsing model's JSON responses
        json_parser = JsonOutputParser(pydantic_object=EvaluationResult)

        correctness_prompt = ChatPromptTemplate.from_messages([
            ("system", CORRECTNESS_PROMPT),
            ("human", "{input}")
        ])
        self.correctness_chain = correctness_prompt | self.llm | json_parser

        groundedness_prompt = ChatPromptTemplate.from_messages([
            ("system", GROUNDEDNESS_PROMPT),
            ("human", "{input}")
        ])
        self.groundedness_chain = groundedness_prompt | self.llm | json_parser

    def evaluate_correctness(self, input):
        return self.correctness_chain.invoke({"input": input})

    def evaluate_groundedness(self, input):
        return self.groundedness_chain.invoke({"input": input})
