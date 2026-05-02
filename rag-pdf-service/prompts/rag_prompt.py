from langchain_core.prompts import ChatPromptTemplate

RAG_PROMPT = ChatPromptTemplate.from_template("""
You are a helpful assistant. Use the following context retrieved from documents
to answer the user's question accurately and concisely.

If the answer is not found in the context, say "I don't have enough information to answer that."

Context:
{context}

Question:
{question}

Answer:
""")

print(RAG_PROMPT.format(context="The capital of France is Paris.", question="What is the capital of France?"))