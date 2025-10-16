from typing import TypedDict
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_ollama import ChatOllama
from langgraph.graph import END, START, StateGraph
from pydantic import BaseModel, Field

from data_processing import VectorialSearch
from prompts import QUESTION_GENERATOR_PROMPT

OLLAMA_BASE_URL = "http://localhost:11434"

class Question(BaseModel):
    question: str = Field(description="A question about the context")
    answer: str = Field(description="The response of the question")

class QuestionList(BaseModel):
    questions: list[Question]

class QuestionGeneratorState(TypedDict):
    query: str
    context: str
    questions: list[Question]

class QuestionGeneratorAgent:
    def __init__(self) -> None:
        self.model = ChatOllama(model='llama3.2:3b', temperature=0.8, base_url=OLLAMA_BASE_URL) \
            .with_structured_output(QuestionList)
        self.search_engine = VectorialSearch()

        self.graph_builder = StateGraph(QuestionGeneratorState)
        
        self.graph_builder.add_node("retrieve_context", self.retrieve_context)
        self.graph_builder.add_node("chatbot", self.chatbot)

        self.graph_builder.add_edge(START, "retrieve_context")
        self.graph_builder.add_edge("retrieve_context", "chatbot")
        self.graph_builder.add_edge("chatbot", END)

    def retrieve_context(self, state: QuestionGeneratorState):
        query = state["query"]
        documents = self.search_engine.search(query, top_k=5)
        context = "\n\n".join([entry["text"] for entry in documents])

        return {"context": context}

    def chatbot(self, state: QuestionGeneratorState):
        context = state["context"]

        instructions = SystemMessage(QUESTION_GENERATOR_PROMPT)
        prompt = HumanMessage(f"Context: {context}")

        response = self.model.invoke([instructions, prompt])
        # print(response)

        return {"questions": response.questions}

    def invoke(self, query):
        agent = self.graph_builder.compile()
        response = agent.invoke({"query": query})

        return response