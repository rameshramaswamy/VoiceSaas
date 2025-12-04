import pytest
import psycopg2
import uuid

DB_DSN = "postgresql://postgres:testpassword@localhost:5432/dtp_core"

def setup_db():
    conn = psycopg2.connect(DB_DSN)
    conn.autocommit = True
    with open("dtp-infra-core/database/schema_rls.sql", "r") as f:
        sql = f.read()
        with conn.cursor() as cur:
            cur.execute(sql)
    conn.close()

def test_tenant_data_isolation():
    setup_db()
    
    # 1. Create Two Tenants
    conn = psycopg2.connect(DB_DSN)
    conn.autocommit = True
    cur = conn.cursor()
    
    tenant_a = str(uuid.uuid4())
    tenant_b = str(uuid.uuid4())
    
    cur.execute("INSERT INTO tenants (id, name) VALUES (%s, 'Tenant A')", (tenant_a,))
    cur.execute("INSERT INTO tenants (id, name) VALUES (%s, 'Tenant B')", (tenant_b,))
    
    # 2. Insert Data as Tenant A
    cur.execute("SELECT set_tenant_context(%s)", (tenant_a,))
    cur.execute("INSERT INTO call_logs (tenant_id, transcript) VALUES (%s, 'Secret A')", (tenant_a,))
    
    # 3. Insert Data as Tenant B
    cur.execute("SELECT set_tenant_context(%s)", (tenant_b,))
    cur.execute("INSERT INTO call_logs (tenant_id, transcript) VALUES (%s, 'Secret B')", (tenant_b,))
    
    # 4. TEST: Query as Tenant A -> Should NOT see Tenant B data
    cur.execute("SELECT set_tenant_context(%s)", (tenant_a,))
    cur.execute("SELECT transcript FROM call_logs")
    results = cur.fetchall()
    
    assert len(results) == 1
    assert results[0][0] == 'Secret A'  # Should only see own data
    
    conn.close()