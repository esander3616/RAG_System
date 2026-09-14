import os
import sqlite3
import pandas as pd

DATA_DIR = "data"
DB_PATH = "capstone_enterprise.db"

TABLES = [
    "monthly_sales",
    "customers",
    "employees",
    "code_review_tickets",
    "expense_requests",
]

def build():
    conn = sqlite3.connect(DB_PATH)
    for table in TABLES:
        csv_path = os.path.join(DATA_DIR, f"{table}.csv")
        if not os.path.exists(csv_path):
            raise FileNotFoundError(
                f"Expected {csv_path} — check DATA_DIR or your CSV filenames."
            )
        df = pd.read_csv(csv_path)
        df.to_sql(table, conn, if_exists="replace", index=False)
        print(f"Loaded {len(df):>5} rows into '{table}'")
    conn.commit()
    conn.close()
    print(f"\nDatabase ready at ./{DB_PATH}")

if __name__ == "__main__":
    build()