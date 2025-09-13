# rag_backend.py
from langchain_community.llms import Ollama
from langchain.prompts import ChatPromptTemplate
from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import OllamaEmbeddings
from langchain.chains import create_retrieval_chain
from langchain.chains.combine_documents import create_stuff_documents_chain

# 1. Define the LLM
llm = Ollama(model="llama3.1")

# 2. Load the vector store
embeddings = OllamaEmbeddings(model="nomic-embed-text")
vectorstore = Chroma(persist_directory="./chroma_db", embedding_function=embeddings)
retriever = vectorstore.as_retriever()

# 3. Create a prompt template
prompt_template = """
You are a helpful and respectful AI assistant for public health queries in Odisha, India.
Your answers should be based only on the context provided below.
If the context does not contain the answer, state clearly that you do not have enough information.
Do not make up information. Provide answers that are concise and easy to understand for a general audience.

Context:
{context}

Question:
{input}

Answer:
"""
prompt = ChatPromptTemplate.from_template(prompt_template)

# 4. Create the RAG chain
question_answer_chain = create_stuff_documents_chain(llm, prompt)
rag_chain = create_retrieval_chain(retriever, question_answer_chain)

def get_rag_response(query: str):
    """
    Gets a response from the RAG chain using the local Llama 3.1 model.
    """
    response = rag_chain.invoke({"input": query})
    return response["answer"]