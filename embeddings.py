from langchain_ollama import ChatOllama
from langchain_ollama import OllamaEmbeddings
from langchain_chroma import Chroma

OLLAMA_BASE_URL = "http://localhost:11434"

question = "O que é o Processo Unificado?"

model = ChatOllama(model='llama3.2:3b', temperature=0, base_url=OLLAMA_BASE_URL)
embeddings = OllamaEmbeddings(model="qwen3-embedding:4b", base_url=OLLAMA_BASE_URL)


vector_store = Chroma(
    collection_name="example_collection",
    embedding_function=embeddings,
    persist_directory="./database", 
)

retrieved_docs = vector_store.similarity_search(question)

print('------Retrieved docs--------')
cleaned_docs = "\n\n".join(doc.page_content for doc in retrieved_docs)
print(cleaned_docs)

response = model.invoke([
        {'role': 'system', 'content': 'You are a helpful professor. Answer the student questions.'},
        {'role': 'user', 'content': f'Context: {cleaned_docs}\nStudent question: {question}'}
    ])

print('------Model Response--------')
print(response)