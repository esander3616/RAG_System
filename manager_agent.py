import os
from dotenv import load_dotenv
from openai import OpenAI
from tokenomics import log_usage
from qualitative_agent import answer_question as ask_qualitative
from quantitative_agent import answer_question as ask_quantitative

load_dotenv()

MODEL = "gemini-3.5-flash-lite"

client = OpenAI(
    api_key=os.getenv("GEMINI_API_KEY"),
    base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
)

CLASSIFY_SYSTEM_PROMPT = """You classify questions for an enterprise assistant
with two specialist agents:

QUALITATIVE: answers questions about documented company policies and
processes (security, code review process, customer complaints, expense
approval rules) by searching policy documents.

QUANTITATIVE: answers questions that require a number computed from a
database (revenue, churn, employee satisfaction scores, code review ticket
turnaround times, expense request amounts) by writing and running SQL.

COMPLEX: the question needs BOTH — for example, it references a policy's
rule AND asks you to check real data against that rule, or it asks for
data plus a recommendation informed by policy.

Think step by step about what the question actually needs answered, not
which keywords it contains. A question can say the word "policy" while its
real ask is a number, or say a number while its real ask is a policy.

Respond with ONLY one word: QUALITATIVE, QUANTITATIVE, or COMPLEX."""

SYNTHESIS_SYSTEM_PROMPT = """Combine the policy finding and the data
finding below into one clear, coherent answer to the user's original
question. Reference specific facts from both. Do not mention that you
consulted separate agents or systems."""

def classify(question: str) -> str:
    completion = client.chat.completions.create(
        model=MODEL,
        temperature=0,
        messages=[
            {"role": "system", "content": CLASSIFY_SYSTEM_PROMPT},
            {"role": "user", "content": question},
        ],
    )
    log_usage("ManagerAgent", completion.usage.prompt_tokens, completion.usage.completion_tokens)
    text = completion.choices[0].message.content.strip().upper()

    if "COMPLEX" in text:
        return "COMPLEX"
    if "QUALITATIVE" in text:
        return "QUALITATIVE"
    if "QUANTITATIVE" in text:
        return "QUANTITATIVE"
    return "COMPLEX"

def synthesize(question: str, qual_answer: str, quant_answer: str) -> str:
    completion = client.chat.completions.create(
        model=MODEL,
        temperature=0.3,
        messages=[
            {"role": "system", "content": SYNTHESIS_SYSTEM_PROMPT},
            {"role": "user", "content": (
                f"Original question: {question}\n\n"
                f"Policy finding: {qual_answer}\n\n"
                f"Data finding: {quant_answer}"
            )},
        ],
    )
    log_usage("ManagerAgent", completion.usage.prompt_tokens, completion.usage.completion_tokens)
    return completion.choices[0].message.content.strip()

def route(question: str) -> dict:
    classification = classify(question)

    if classification == "QUALITATIVE":
        result = ask_qualitative(question)
        return {"question": question, "classification": classification, "answer": result["answer"]}

    if classification == "QUANTITATIVE":
        result = ask_quantitative(question)
        return {"question": question, "classification": classification, "answer": result["answer"]}

    qual_result = ask_qualitative(question)
    quant_result = ask_quantitative(question, extra_context=qual_result["answer"])

    if quant_result.get("valid") and not quant_result.get("rows"):
        clarified_question = (
            f"{question}\n\n(Note: a previous attempt at this query "
            f"returned zero rows, which likely means a filter or date "
            f"range was wrong rather than the true answer being zero. "
            f"Double-check column names, value spellings, and date "
            f"formats against the schema, and broaden the query if needed.)"
        )
        quant_result = ask_quantitative(clarified_question, extra_context=qual_result["answer"])

    final_answer = synthesize(question, qual_result["answer"], quant_result["answer"])

    return {
        "question": question,
        "classification": classification,
        "answer": final_answer,
        "qualitative_answer": qual_result["answer"],
        "quantitative_answer": quant_result["answer"],
        "sql": quant_result.get("sql"),
    }

if __name__ == "__main__":
    for q in [
        "What is our company's security policy?",
        "What's our customer churn rate?",
        "What's our policy on expense approvals, and how many expense "
        "requests last quarter would have required manager sign-off "
        "under that policy?",
    ]:
        result = route(q)
        print(f"\nQ: {result['question']}")
        print(f"Classification: {result['classification']}")
        if result.get("sql"):
            print(f"SQL: {result['sql']}")
        print(f"A: {result['answer']}")