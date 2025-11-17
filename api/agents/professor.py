from os import getenv
import asyncio
import json
from langchain_ollama import ChatOllama
from langgraph.checkpoint.postgres import PostgresSaver
from langchain_core.messages import AIMessageChunk, HumanMessage, SystemMessage, ToolMessage
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.postgres import PostgresSaver
from langgraph.prebuilt import tools_condition
from prompts import MAIN_MODEL_PROMPT
from data_processing import VectorStore
from typing_extensions import TypedDict
from toolbox import generate_study_questions, search_documents


OLLAMA_BASE_URL = getenv("OLLAMA_BASE_URL")
POSTGRES_URL = getenv("POSTGRES_URL")
MONGO_URL = getenv("MONGO_URL")
PROFESSOR_MODEL = getenv("PROFESSOR_MODEL")

class State(TypedDict):
    messages: list
    context: str


class ToolNode:
    def __init__(self, tools: list) -> None:
        self.tools_by_name = {tool.name: tool for tool in tools}


    def __call__(self, state: State):
        if messages := state.get("messages", []):
            message = messages[-1]
        else:
            raise ValueError("No message found in input")
        outputs = []
        for tool_call in message.tool_calls:
            tool_result = self.tools_by_name[tool_call["name"]].invoke(
                tool_call["args"]
            )
            outputs.append(
                ToolMessage(
                    content=tool_result,
                    name=tool_call["name"],
                    tool_call_id=tool_call["id"],
                )
            )

        state["messages"] = state["messages"] + outputs

        return state

class ProfessorAgent:
    def __init__(self) -> None:
        self.search_engine = VectorStore()
        
        tools = [generate_study_questions, search_documents]

        self.model = ChatOllama(model=PROFESSOR_MODEL, base_url=OLLAMA_BASE_URL, reasoning=False)
        self.model = self.model.bind_tools(tools)

        self.graph_builder = StateGraph(State)

        tools_node = ToolNode(tools)

        self.graph_builder.add_node("inject_prompt", self.inject_prompt)
        self.graph_builder.add_node("chatbot", self.chatbot)
        self.graph_builder.add_node("tools", tools_node)

        self.graph_builder.add_edge(START, "inject_prompt")
        self.graph_builder.add_edge("inject_prompt", "chatbot")

        self.graph_builder.add_conditional_edges("chatbot", tools_condition)
        self.graph_builder.add_edge("tools", "chatbot")

    @staticmethod
    def checkpointer():
        return PostgresSaver.from_conn_string(POSTGRES_URL)

    def inject_prompt(self, state: State):
        messages = state.get("messages", [])

        if not any(isinstance(msg, SystemMessage) for msg in messages):
            system_prompt = SystemMessage(
                content=MAIN_MODEL_PROMPT
            )
            messages.insert(0, system_prompt)

        state["messages"] = messages

        return state

    def retrieve_context(self, state: State):
        documents = self.search_engine.search(state["messages"][-1].content)
        context = "\n\n".join([entry["text"] for entry in documents])

        state["context"] = context
        return state

    def chatbot(self, state: State):
        last_message = state["messages"][-1]

        if isinstance(last_message, HumanMessage):
            # context = state["context"]
            query = last_message.content
            prompt = query

            llm_response = self.model.invoke(state["messages"][:-1] + [HumanMessage(content=prompt)])
            state["messages"].append(llm_response)
        else:
            llm_response = self.model.invoke(state["messages"])
            state["messages"].append(llm_response)

        return state
    
    def inject_context(self, state: State):
        last_message = state["messages"][-1]
        last_message.additional_kwargs["context"] = state["context"]
        state["messages"] = state["messages"][:-1] + [last_message]

        return state
        
    def create_messages(self, query, context):
        return {"messages": [{
            "role": "user", 
            "content": f"Context: {context}\n\nUser Question: {query}",
            "metadata": {"context": context, "query": query}
            }]}
    
    async def ainvoke_graph(self, query, thread_id):
        with ProfessorAgent.checkpointer() as checkpointer:
            agent = self.graph_builder.compile(checkpointer=checkpointer)
            config = {"configurable": {"thread_id": thread_id}}
            messages = [HumanMessage(content=query)]

            if previous_messages := agent.get_state(config)[0].get("messages"):
                messages = previous_messages + messages

            response_stream = agent.stream(
                {"messages": messages},
                config=config,
                stream_mode="messages"
            )

            for chunk in response_stream:
                message = chunk[0]
                if isinstance(message, AIMessageChunk):
                    json_message = {
                        "content": message.content,
                        "additional_kwargs": message.additional_kwargs
                    }
                    yield f"data: {json.dumps(json_message)}\n\n"
                    await asyncio.sleep(0)
                else:
                    print(f"Unknown object in stream: {type(message)}")

    def get_conversation(self, config):
        with ProfessorAgent.checkpointer() as checkpointer:
            graph = self.graph_builder.compile(checkpointer=checkpointer)
            return graph.get_state(config)