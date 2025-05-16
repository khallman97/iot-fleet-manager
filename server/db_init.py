import psycopg2
import os

DATABASE_URL = os.environ.get("DATABASE_URL", "postgresql://postgres:password@localhost:5432/postgres")


def db_init():
    # Connect once when app starts
    conn = psycopg2.connect(DATABASE_URL)
    conn.autocommit = True
    cur = conn.cursor()

    # Create the metrics table and hypertable if not exists
    cur.execute("""
    CREATE TABLE IF NOT EXISTS pi_metrics (
        time TIMESTAMPTZ NOT NULL,
        hostname TEXT NOT NULL,
        cpu_percent FLOAT,
        memory_used BIGINT,
        memory_total BIGINT,
        disk_used BIGINT,
        disk_total BIGINT,
        uptime BIGINT,
        PRIMARY KEY (time, hostname)
    );
    """)

    # Create hypertable if not exists
    cur.execute("""
    SELECT create_hypertable('pi_metrics', 'time', if_not_exists => TRUE);
    """)
