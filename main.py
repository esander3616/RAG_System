"""
Type a question about company policy, company data, or both. Type
'summary' at any time to see the tokenomics report so far, or
'exit' / 'quit' to leave (a final summary prints automatically).
"""

from manager_agent import route
from tokenomics import summarize

def print_banner():
    print("=" * 64)
    print("  Multi-Agent RAG System — Enterprise Documentation Assistant")
    print("=" * 64)
    print("Ask about company policy, company data, or both.")
    print("Commands: 'summary' for token usage, 'exit' to quit.\n")

def main():
    print_banner()
    query_count = 0

    while True:
        try:
            question = input("You: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nGoodbye.")
            break

        if not question:
            continue

        if question.lower() in ("exit", "quit"):
            print("Goodbye.")
            break

        if question.lower() == "summary":
            summarize()
            print()
            continue

        result = route(question)
        query_count += 1

        print(f"\n[{result['classification']}]")
        if result.get("sql"):
            print(f"(SQL: {result['sql']})")
        print(f"Assistant: {result['answer']}\n")

    print(f"\nSession complete — {query_count} question(s) answered.")
    if query_count > 0:
        print("\nFinal tokenomics summary:")
        summarize()

if __name__ == "__main__":
    main()