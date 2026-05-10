import os
from langsmith import traceable
from langchain_groq import ChatGroq
from langchain_core.output_parsers import StrOutputParser
from prompts.eval_prompt import EVAL_PROMPT
from dotenv import load_dotenv

load_dotenv()

@traceable(run_type="chain")
def evaluate_response(question: str, reference: str, answer: str, history_context: str = "") -> dict:
    """
    Uses a separate LLM instance as an evaluator/judge.
    Returns verdict: 'correct' or 'incorrect' with confidence details.
    
    Args:
        question: The user's question
        reference: Document context used for the answer
        answer: The AI's response
        history_context: Previous conversation history (if any)
    """
    # ✅ Separate evaluator LLM — can be different model than the main one
    evaluator_llm = ChatGroq(
        model="llama-3.3-70b-versatile",   # larger model as judge
        api_key=os.getenv("GROQ_API_KEY"),
        temperature=0,                      # deterministic — we want strict correct/incorrect
        max_tokens=5,                       # only needs 1 word — saves tokens
    )

    chain = EVAL_PROMPT | evaluator_llm | StrOutputParser()

    # Combine document context with history context for evaluation
    full_context = reference
    if history_context:
        full_context = f"{history_context}\n\nDocument context:\n{reference}"

    raw = chain.invoke({
        "question":  question,
        "reference": full_context,
        "answer":    answer,
    })

    verdict = raw.strip().lower()

    # Guard against unexpected output
    if verdict not in ("correct", "incorrect"):
        verdict = "incorrect"

    return {
        "verdict":   verdict,
        "is_correct": verdict == "correct",
        "raw_output": raw.strip(),
    }