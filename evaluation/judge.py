from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from pydantic import BaseModel
from typing import Literal
from prompts import CORRECTNESS_PROMPT, GROUNDEDNESS_PROMPT
from os import getenv
from dotenv import load_dotenv

load_dotenv()

class EvaluationResult(BaseModel):
    analysis: str
    verdict: Literal["good", "satisfactory", "unsatisfactory"]


class Judge:
    def __init__(
        self,
        temperature=0.0
    ):
        self.temperature = temperature

        self.llm = ChatGroq(
            model="openai/gpt-oss-120b",
            temperature=temperature
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
