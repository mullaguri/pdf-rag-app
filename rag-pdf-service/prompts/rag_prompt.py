from langchain_core.prompts import ChatPromptTemplate

RAG_PROMPT = ChatPromptTemplate.from_template("""
You are a helpful assistant. Use the following context to answer the user's question accurately and concisely.

The context includes:
1. Previous conversation history (if any)
2. Relevant information retrieved from documents

When answering:
- Use the conversation history to understand the context and follow-up questions
- Reference previous exchanges when relevant to provide coherent responses
- Use the document information to provide accurate answers
- If the answer is not found in the documents or history, say "I don't have enough information to answer that."

Context:
{context}

Question:
{question}

Answer:
""")

print(RAG_PROMPT.format(context="The capital of France is Paris.", question="What is the capital of France?"))