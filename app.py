import os
import fitz  # PyMuPDF
import streamlit as st
import google.generativeai as genai
import numpy as np
from dotenv import load_dotenv
from langchain_text_splitters import CharacterTextSplitter
from langchain.vectorstores import FAISS
from langchain.embeddings.base import Embeddings
from langchain.chains import RetrievalQA

from dotenv import load_dotenv
load_dotenv()


# Embeddings class
class GeminiEmbedding(Embeddings):
    def embed_documents(self, texts):
        return [genai.embed_content(
                    model="models/embedding-001",
                    content=text,
                    task_type="retrieval_document"
                )["embedding"] for text in texts]

    def embed_query(self, text):
        return genai.embed_content(
            model="models/embedding-001",
            content=text,
            task_type="retrieval_query"
        )["embedding"]


# PDF extractor
@st.cache_resource
def extract_text(path):
    doc = fitz.open(path)
    return "".join(page.get_text() for page in doc)

# Embed text chunks and create FAISS index
@st.cache_resource
def build_vector_store(text):
    splitter = CharacterTextSplitter(
    separator="\n",
    chunk_size=2000,
    chunk_overlap=200,
    length_function=len
    )
    chunks = splitter.split_text(text)
    embeddings = GeminiEmbedding()
    return FAISS.from_texts(chunks, embedding=embeddings)

# Load Gemini model
#llm = genai.GenerativeModel("models/gemini-1.5-flash-latest")  gemini-pro
from langchain_google_genai import ChatGoogleGenerativeAI

llm = ChatGoogleGenerativeAI(model="gemini-1.5-flash-latest")


# Streamlit UI
st.set_page_config(page_title="📖 Crime & Punishment RAG", layout="centered")
st.title("📚 Ask About *Crime and Punishment*")

# Load and process PDF
with st.spinner("📄 Reading and indexing PDF..."):
    full_text = extract_text("Crime-and-Punishment.pdf")
    db = build_vector_store(full_text)
    qa = RetrievalQA.from_chain_type(llm=llm, retriever=db.as_retriever())

# User query
question = st.text_input("💬 Ask a question", placeholder="e.g., Who is Raskolnikov?")
if question:
    with st.spinner("🤔 Thinking..."):
        response = qa.run(question)
        st.success(response)
