-- 1. Create Audit Log Table
CREATE TABLE IF NOT EXISTS audit_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    table_name TEXT NOT NULL,
    operation VARCHAR(10) NOT NULL, -- INSERT, UPDATE, DELETE
    record_id UUID,
    tenant_id UUID,
    old_values JSONB,
    new_values JSONB,
    changed_by VARCHAR(255), -- The system user or API key ID
    changed_at TIMESTAMP DEFAULT NOW()
);

-- 2. Audit Trigger Function
CREATE OR REPLACE FUNCTION audit_trigger_func()
RETURNS TRIGGER AS $$
DECLARE
    current_tenant UUID;
BEGIN
    -- Capture the current tenant context safely
    BEGIN
        current_tenant := current_setting('app.current_tenant')::uuid;
    EXCEPTION WHEN OTHERS THEN
        current_tenant := NULL;
    END;

    IF (TG_OP = 'INSERT') THEN
        INSERT INTO audit_logs (table_name, operation, record_id, tenant_id, new_values, changed_by)
        VALUES (TG_TABLE_NAME, 'INSERT', NEW.id, current_tenant, row_to_json(NEW), current_user);
        RETURN NEW;
    ELSIF (TG_OP = 'UPDATE') THEN
        INSERT INTO audit_logs (table_name, operation, record_id, tenant_id, old_values, new_values, changed_by)
        VALUES (TG_TABLE_NAME, 'UPDATE', NEW.id, current_tenant, row_to_json(OLD), row_to_json(NEW), current_user);
        RETURN NEW;
    ELSIF (TG_OP = 'DELETE') THEN
        INSERT INTO audit_logs (table_name, operation, record_id, tenant_id, old_values, changed_by)
        VALUES (TG_TABLE_NAME, 'DELETE', OLD.id, current_tenant, row_to_json(OLD), current_user);
        RETURN OLD;
    END IF;
    RETURN NULL;
END;
$$ LANGUAGE plpgsql;

-- 3. Apply to Critical Tables
DROP TRIGGER IF EXISTS trg_audit_tenants ON tenants;
CREATE TRIGGER trg_audit_tenants
AFTER INSERT OR UPDATE OR DELETE ON tenants
FOR EACH ROW EXECUTE FUNCTION audit_trigger_func();