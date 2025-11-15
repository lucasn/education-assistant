from langchain_ollama import ChatOllama
from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel
from typing import Literal
from .prompts import CORRECTNESS_PROMPT, GROUNDEDNESS_PROMPT


class EvaluationResult(BaseModel):
    analysis: str
    verdict: Literal["good", "satisfactory", "unsatisfactory"]


class Judge:
    def __init__(
        self,
        model="llama3.2",
        base_url="http://localhost:11434",
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
            **kwargs
        )

        structured_llm = self.llm.with_structured_output(EvaluationResult)

        correctness_prompt = ChatPromptTemplate.from_messages([
            ("system", CORRECTNESS_PROMPT),
            ("human", "{input}")
        ])
        self.correctness_chain = correctness_prompt | structured_llm

        groundedness_prompt = ChatPromptTemplate.from_messages([
            ("system", GROUNDEDNESS_PROMPT),
            ("human", "{input}")
        ])
        self.groundedness_chain = groundedness_prompt | structured_llm

    def evaluate_correctness(self, input):
        return self.correctness_chain.invoke({"input": input})

    def evaluate_groundedness(self, input):
        return self.groundedness_chain.invoke({"input": input})
