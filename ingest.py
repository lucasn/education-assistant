
import pymupdf
from langchain_ollama import OllamaEmbeddings
from langchain_chroma import Chroma
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter


DOCUMENT_PATH = "./data/document.pdf"
OLLAMA_BASE_URL = "http://localhost:11434"

doc = pymupdf.open(DOCUMENT_PATH)
doc_text = ""
for i, page in enumerate(doc): 
    text = page.get_text() 
    doc_text += text

    # images = page.get_images()

    # if images:
    #     print(f"Found {len(images)} images on page {i}")
    # else:
    #     print("No images found on page", i)

    # for j, image in enumerate(images):
    #     print(f'Image {j}')
    #     xref = image[0] 
    #     pix = pymupdf.Pixmap(doc, xref)

    #     if pix.n - pix.alpha > 3: 
    #         pix = pymupdf.Pixmap(pymupdf.csRGB, pix)

    #     pix.save("./data/page_%s-image_%s.png" % (i, j))
    #     pix = None

print(doc_text)

documents = [Document(page_content=doc_text)]

embeddings = OllamaEmbeddings(model="qwen3-embedding:4b", base_url=OLLAMA_BASE_URL)

vector_store = Chroma(
    collection_name="example_collection",
    embedding_function=embeddings,
    persist_directory="./database",  # Where to save data locally, remove if not necessary
)

from langchain_text_splitters import RecursiveCharacterTextSplitter

text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=1000, chunk_overlap=200, add_start_index=True
)
all_splits = text_splitter.split_documents(documents)
_ = vector_store.add_documents(documents=all_splits)
