import psycopg2

TESTS = [
    dict(user="postgres", password="postgres"),
    dict(user="gchub", password="gchub"),
]

for t in TESTS:
    try:
        print("Trying", t)
        conn = psycopg2.connect(
            dbname="gchub_dev",
            user=t["user"],
            password=t["password"],
            host="127.0.0.1",
            port=5433,
            connect_timeout=5,
        )
        cur = conn.cursor()
        cur.execute("SELECT 1")
        print("OK", t)
        cur.close()
        conn.close()
    except Exception as e:
        print("ERR", t, type(e).__name__, e)
