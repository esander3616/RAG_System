from sql_validation import validate_sql

# (description, query, expected_valid)
CASES = [
    ("Blocks DROP TABLE",
     "DROP TABLE customers;", False),

    ("Blocks DELETE",
     "DELETE FROM customers WHERE customer_id = 1;", False),

    ("Blocks UPDATE",
     "UPDATE customers SET is_churned = 1 WHERE customer_id = 5;", False),

    ("Blocks INSERT",
     "INSERT INTO customers (customer_id, region) VALUES (1001, 'APAC');", False),

    ("Blocks non-SELECT statements not in the keyword list",
     "PRAGMA table_info(customers);", False),

    ("Allows a simple legitimate SELECT",
     "SELECT * FROM customers WHERE region = 'APAC';", True),

    ("Allows a legitimate SELECT with aggregation",
     "SELECT region, SUM(revenue) FROM monthly_sales GROUP BY region;", True),

    ("Allows a SELECT containing a blocked word as a substring (no false positive)",
     "SELECT * FROM expense_requests WHERE category LIKE '%DROPBOX%';", True),
]


def run():
    passed = 0
    for description, query, expected in CASES:
        result = validate_sql(query)
        ok = result["valid"] == expected
        status = "PASS" if ok else "FAIL"
        print(f"[{status}] {description}")
        print(f"       query:    {query}")
        print(f"       expected: valid={expected}  got: {result}\n")
        passed += ok

    print(f"{passed}/{len(CASES)} test cases passed")
    if passed != len(CASES):
        raise SystemExit(1)


if __name__ == "__main__":
    run()