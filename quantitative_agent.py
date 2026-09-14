import os
import sqlite3
from datetime import date, timedelta
from dotenv import load_dotenv
from openai import OpenAI
from sql_validation import validate_sql
from tokenomics import log_usage
load_dotenv()

MODEL = "gemini-3.5-flash-lite"
DB_PATH = "capstone_enterprise.db"

client = OpenAI(
    api_key=os.getenv("GEMINI_API_KEY"),
    base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
)

def last_complete_quarter_bounds(today: date | None = None) -> tuple[str, str]:
    """Returns (start, end) as YYYY-MM-DD for the most recently completed
    calendar quarter relative to today. Computed in Python, not guessed by
    the model, so 'last quarter' resolves to the same dates every time."""
    today = today or date.today()
    current_q = (today.month - 1) // 3 + 1
    year, quarter = (today.year - 1, 4) if current_q == 1 else (today.year, current_q - 1)
    start_month = (quarter - 1) * 3 + 1
    start = date(year, start_month, 1)
    end_month = start_month + 2
    end = date(year, 12, 31) if end_month == 12 else date(year, end_month + 1, 1) - timedelta(days=1)
    return start.isoformat(), end.isoformat()

SCHEMA_DESCRIPTION = """
monthly_sales(year INT, month INT, region TEXT, revenue REAL, units_sold INT, new_customers INT)
  region is one of: 'North America', 'EMEA', 'APAC', 'LATAM'

customers(customer_id INT, signup_date TEXT, region TEXT, plan_type TEXT,
          monthly_charge REAL, is_churned INT, churn_date TEXT)
  plan_type is one of: 'Basic', 'Pro', 'Enterprise'. is_churned is 0 or 1.

employees(employee_id INT, department TEXT, region TEXT, hire_date TEXT,
          satisfaction_score REAL, is_active INT)
  department is one of: 'Engineering', 'Sales', 'Customer Support', 'Finance', 'HR', 'Marketing'

code_review_tickets(ticket_id INT, team TEXT, opened_at TEXT, closed_at TEXT,
                     status TEXT, turnaround_hours REAL)
  team is one of: 'Platform', 'Backend', 'Frontend', 'Mobile', 'Data Infrastructure'
  status is 'Open' or 'Closed'

expense_requests(request_id INT, employee_id INT, department TEXT,
                  submitted_date TEXT, amount REAL, category TEXT, status TEXT)
  status is one of: 'Approved', 'Pending', 'Rejected'
"""

def build_sql_system_prompt() -> str:
    today_str = date.today().isoformat()
    q_start, q_end = last_complete_quarter_bounds()
    return f"""You are a SQL generator for a SQLite database.
Given a natural language question, output ONLY a single valid SQLite
SELECT query that answers it. No explanation, no markdown code fences,
no multiple statements. Only SELECT is permitted.

Today's date is {today_str}. Resolve relative date references yourself,
in the query, rather than leaving them for the caller to interpret:
- "last quarter" / "the most recent complete quarter" means the date
  range {q_start} to {q_end} inclusive.
- For other relative ranges (last month, this year, etc.), compute the
  actual calendar boundary from today's date above rather than using
  SQLite's date('now', ...) modifiers, which drift from calendar
  boundaries and should be avoided here.

Never write a query that returns a fixed text string or explanation
instead of real data (e.g. SELECT 'no data available' AS answer) — if
only part of the question can be answered from this schema (for example
it references an external benchmark that isn't in these tables), still
write a real query against whatever part of the question the schema
CAN answer, and let the caller note the missing part separately.

Never collapse a metric into a bare boolean comparison (e.g.
SELECT AVG(x) <= 48). Return the actual computed value (a percentage,
count, or average) so the magnitude is visible, not just true/false.

Tables:
{SCHEMA_DESCRIPTION}
"""

INSIGHT_SYSTEM_PROMPT = """You are a data analyst. Given a user's question
and raw SQL query results, write a short 2-4 sentence plain-language
answer that references specific numbers from the results. Do not mention
SQL, databases, or queries."""

def generate_sql(question: str, extra_context: str = "") -> str:
    user_content = question
    if extra_context:
        user_content = (
            f"Relevant policy context (use any numeric thresholds from this "
            f"in your WHERE clause if relevant):\n{extra_context}\n\n"
            f"Question: {question}"
        )
    completion = client.chat.completions.create(
        model=MODEL,
        temperature=0,
        messages=[
            {"role": "system", "content": build_sql_system_prompt()},
            {"role": "user", "content": user_content},
        ],
    )
    log_usage("QuantitativeAgent", completion.usage.prompt_tokens, completion.usage.completion_tokens)
    sql = completion.choices[0].message.content.strip()
    return sql.replace("```sql", "").replace("```", "").strip()

def run_query(sql: str) -> list[dict]:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        rows = [dict(r) for r in conn.execute(sql).fetchall()]
    finally:
        conn.close()
    return rows

def generate_insight(question: str, rows: list[dict]) -> str:
    completion = client.chat.completions.create(
        model=MODEL,
        temperature=0.3,
        messages=[
            {"role": "system", "content": INSIGHT_SYSTEM_PROMPT},
            {"role": "user", "content": f"Question: {question}\nResults: {rows}"},
        ],
    )
    log_usage("QuantitativeAgent", completion.usage.prompt_tokens, completion.usage.completion_tokens)
    return completion.choices[0].message.content.strip()

def answer_question(question: str, extra_context: str = "") -> dict:
    """Full pipeline. Returns a dict either way so callers never have to
    guess what shape the response is in. extra_context, if provided
    (e.g. from the Qualitative Agent), gets folded into SQL generation —
    used for complex queries that need a policy threshold applied to data."""
    sql = generate_sql(question, extra_context)

    validation = validate_sql(sql)
    if not validation["valid"]:
        return {
            "question": question, "sql": sql, "valid": False,
            "answer": f"I couldn't safely run that query: {validation['reason']}",
        }

    try:
        rows = run_query(sql)
    except sqlite3.Error as e:
        return {
            "question": question, "sql": sql, "valid": True,
            "answer": f"The generated query failed to execute: {e}",
        }

    return {
        "question": question, "sql": sql, "valid": True,
        "rows": rows, "answer": generate_insight(question, rows),
    }

if __name__ == "__main__":
    for q in [
        "What is our customer churn rate?",
        "Compare Q4 revenue across regions for 2024 and 2025",
        "What is the average employee satisfaction score by department?",
    ]:
        result = answer_question(q)
        print(f"\nQ: {result['question']}")
        print(f"SQL: {result['sql']}")
        print(f"A: {result['answer']}")