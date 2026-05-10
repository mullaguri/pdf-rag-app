from langchain_core.prompts import PromptTemplate

EVAL_PROMPT = PromptTemplate(
    input_variables=["question", "reference", "answer"],
    template="""You are given a question, an answer and reference text. The reference may include \
previous conversation history followed by document context. You must determine whether the given answer correctly \
answers the question based on the reference text. Here is the data:
[BEGIN DATA]
************
[Question]: {question}
************
[Reference]: {reference}
************
[Answer]: {answer}
[END DATA]
Your response must be a single word, either "correct" or "incorrect", and should not contain any text \
or characters aside from that word. "correct" means that the question is correctly and fully answered \
by the answer. "incorrect" means that the question is not correctly or only partially answered by the answer."""
)