import psycopg2

conn = psycopg2.connect(dbname="gchub_dev", user="postgres", password="postgres", host="localhost")
cur = conn.cursor()
cur.execute("SELECT schemaname, tablename FROM pg_tables ORDER BY schemaname, tablename;")
rows = cur.fetchall()
print("tables:", rows[:20])
cur.execute("SELECT count(*) FROM information_schema.tables WHERE table_schema='public';")
print("public_table_count:", cur.fetchone())
# check migrations table
try:
    cur.execute("SELECT count(*) FROM django_migrations;")
    print("django_migrations:", cur.fetchone())
except Exception as e:
    print("django_migrations not found or error:", e)
cur.close()
conn.close()
