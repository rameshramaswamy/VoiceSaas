-- 1. Tenants Table
CREATE TABLE IF NOT EXISTS tenants (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    status VARCHAR(50) DEFAULT 'active',
    created_at TIMESTAMP DEFAULT NOW()
);

-- 2. Sensitive Data Table (Example)
CREATE TABLE IF NOT EXISTS call_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID REFERENCES tenants(id),
    transcript TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);

-- 3. ENABLE RLS
ALTER TABLE call_logs ENABLE ROW LEVEL SECURITY;

-- 4. Create Security Policy
-- This policy forces every query to check if the row's tenant_id 
-- matches the session variable 'app.current_tenant'
CREATE POLICY tenant_isolation_policy ON call_logs
    FOR ALL
    USING (tenant_id = current_setting('app.current_tenant')::uuid);

-- 5. Helper function to set context
CREATE OR REPLACE FUNCTION set_tenant_context(tenant_uuid UUID)
RETURNS void AS $$
BEGIN
    PERFORM set_config('app.current_tenant', tenant_uuid::text, false);
END;
$$ LANGUAGE plpgsql;