"""OpenAI-equivalent Retrieval-Augmented Generation (RAG) pipeline.

Mirrors rag.py's pipeline shape (load PDF -> chunk -> embed -> retrieve ->
generate), but backed by OpenAI instead of Fireworks:
- Embeds chunks with OpenAI's `text-embedding-3-small` and stores vectors
  in an in-memory Qdrant store.
- Generates answers with OpenAI's `gpt-4.1-mini`, constrained to the
  retrieved context.

Unlike rag.py's `retrieve_information`, this isn't exposed as a LangChain
`@tool` for an agent to call. `answer_with_openai_rag()` instead returns
both the generated response and the raw retrieved context chunks, so it
can be used directly in the Activity 1 RAGAS evaluation to compare against
the Fireworks-powered pipeline.
"""

from __future__ import annotations

import os
from functools import lru_cache
from typing import TypedDict

import tiktoken
from langchain_community.document_loaders import DirectoryLoader, PyMuPDFLoader
from langchain_core.documents import Document
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from langchain_openai.embeddings import OpenAIEmbeddings
from langchain_qdrant import QdrantVectorStore
from langgraph.graph import START, StateGraph



def _tiktoken_len(text: str) -> int:
    """Return token length using tiktoken; used for chunk length measurement."""
    tokens = tiktoken.encoding_for_model("gpt-4o").encode(text)
    return len(tokens)


class _RAGState(TypedDict):
    """State schema for the simple two-step RAG graph: retrieve then generate."""

    question: str
    context: list[Document]
    response: str


def _build_openai_rag_graph(data_dir: str):
    """Construct and compile a minimal RAG graph.

    Steps:
    1) Load PDFs from `data_dir` recursively (best-effort).
    2) Split documents into token-aware chunks.
    3) Create embeddings and an in-memory Qdrant vector store retriever.
    4) Define a chat prompt and generation model.
    5) Wire a two-node graph: retrieve -> generate.
    """
    # Load PDFs from data directory (recursive)
    try:
        directory_loader = DirectoryLoader(
            data_dir, glob="**/*.pdf", loader_cls=PyMuPDFLoader
        )
        documents = directory_loader.load()
    except Exception:
        documents = []

    # Split documents
    from langchain_text_splitters import RecursiveCharacterTextSplitter

    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=750, chunk_overlap=0, length_function=_tiktoken_len
    )
    chunks = text_splitter.split_documents(documents) if documents else []

    # Embeddings and vector store (in-memory Qdrant)
    embedding_model = OpenAIEmbeddings(
        model="text-embedding-3-small",
        openai_api_key=os.environ["OPENAI_API_KEY"],
    )
    qdrant_vectorstore = QdrantVectorStore.from_documents(
        documents=chunks,
        embedding=embedding_model,
        location=":memory:",
        collection_name="rag_collection",
    )
    retriever = qdrant_vectorstore.as_retriever()

    # Prompt and model
    human_template = (
        "\n#CONTEXT:\n{context}\n\nQUERY:\n{query}\n\n"
        "Use the provide context to answer the provided user query. "
        "Only use the provided context to answer the query. If you do not know the answer, or it's not contained in the provided context respond with \"I don't know\""
    )
    chat_prompt = ChatPromptTemplate.from_messages([("human", human_template)])
    generator_llm = ChatOpenAI(
        model="gpt-4.1-mini",
        openai_api_key=os.environ["OPENAI_API_KEY"],
    )

    def retrieve(state: _RAGState) -> _RAGState:
        retrieved_docs = retriever.invoke(state["question"]) if retriever else []
        return {"context": retrieved_docs}  # type: ignore

    def generate(state: _RAGState) -> _RAGState:
        generator_chain = chat_prompt | generator_llm | StrOutputParser()
        response_text = generator_chain.invoke(
            {"query": state["question"], "context": state.get("context", [])}
        )
        return {"response": response_text}  # type: ignore

    graph_builder = StateGraph(_RAGState)
    graph_builder = graph_builder.add_sequence([retrieve, generate])
    graph_builder.add_edge(START, "retrieve")
    return graph_builder.compile()


@lru_cache(maxsize=1)
def _get_openai_rag_graph():
    """Return a cached compiled RAG graph built from RAG_DATA_DIR."""
    data_dir = os.environ.get("RAG_DATA_DIR", "data")
    return _build_openai_rag_graph(data_dir)

def answer_with_openai_rag(question: str) -> dict:
    graph = _get_openai_rag_graph()
    result = graph.invoke(
    {"question": question},
    config={"metadata": {"pipeline": "openai"}},
    )
    return {
        "response": result.get("response", ""),
        "context": [doc.page_content for doc in result.get("context", [])],
    }