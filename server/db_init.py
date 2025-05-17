import psycopg2
from psycopg2.extras import execute_values
import os
import time

# Read DB connection info from environment or config
DB_HOST = os.getenv('DB_HOST', 'localhost')
DB_PORT = os.getenv('DB_PORT', '5432')
DB_NAME = os.getenv('DB_NAME', 'pi_metrics')
DB_USER = os.getenv('DB_USER', 'postgres')
DB_PASS = os.getenv('DB_PASS', 'password')
DATABASE_URL = os.getenv("DATABASE_URL", 'postgresql://postgres:password@timescaledb:5432/postgres')

conn = None

def connect_db():
    global conn
    retries = 5
    while retries > 0:
        try:
            conn = psycopg2.connect(
                DATABASE_URL
            )
            print("Connected to DB")
            return
        except Exception as e:
            print(f"DB connection failed: {e}. Retrying in 3s...")
            retries -= 1
            time.sleep(3)
    raise Exception("Could not connect to DB")

def run_sql(sql):
    with conn.cursor() as cur:
        conn.autocommit = True
        cur.execute(sql)
        conn.autocommit = False

def init_db():
    # Create extension if not exists
    run_sql("CREATE EXTENSION IF NOT EXISTS timescaledb;")

    # Create main table (hypertable)
    run_sql("""
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

    # Generte wg_key storage table
    run_sql("""
        CREATE TABLE IF NOT EXISTS pi_wireguard_keys (
        id SERIAL PRIMARY KEY,
        hostname TEXT UNIQUE NOT NULL,
        wg_ip INET NOT NULL,                        
        public_key TEXT NOT NULL,                   
        private_key BYTEA NOT NULL,                  
        server_public_key TEXT NOT NULL,           
        server_endpoint TEXT NOT NULL,               
        created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
    );
    """)

    # Create hypertable if not exists
    run_sql("""
    SELECT create_hypertable('pi_metrics', 'time', if_not_exists => TRUE);
    """)

    # Create continuous aggregate
    run_sql("""
    CREATE MATERIALIZED VIEW IF NOT EXISTS pi_metrics_4h
    WITH (timescaledb.continuous) AS
    SELECT
        time_bucket('4 hours', time) AS bucket,
        hostname,
        avg(cpu_percent) AS avg_cpu_percent,
        avg(memory_used) AS avg_memory_used,
        avg(memory_total) AS avg_memory_total,
        avg(disk_used) AS avg_disk_used,
        avg(disk_total) AS avg_disk_total,
        avg(uptime) AS avg_uptime
    FROM pi_metrics
    WHERE time < NOW() - INTERVAL '24 hours'
    GROUP BY bucket, hostname;
    """)

    # Add continuous aggregate refresh policy
    run_sql("""
    SELECT add_continuous_aggregate_policy('pi_metrics_4h',
        start_offset => INTERVAL '30 days',
        end_offset => INTERVAL '24 hours',
        schedule_interval => INTERVAL '1 hour');
    """)

    # Add retention policy (drop raw data older than 15 days)
    run_sql("""
    SELECT add_retention_policy('pi_metrics', INTERVAL '15 days');
    """)

    print("DB initialized with hypertable, continuous aggregate, policies.")

def main():
    connect_db()
    init_db()
    conn.close()

if __name__ == "__main__":
    main()
