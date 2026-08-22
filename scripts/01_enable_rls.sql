-- ReconGraph: Postgres Row-Level Security (RLS) Setup
-- This script hardens the database by enforcing strict tenant isolation at the kernel level.
-- Even if application code has a bug (e.g. missing `WHERE tenant_id = ?`), 
-- the database will physically prevent cross-tenant data bleed.

-- 1. Enable RLS on core tables
ALTER TABLE purchase_register ENABLE ROW LEVEL SECURITY;
ALTER TABLE gst_register ENABLE ROW LEVEL SECURITY;
ALTER TABLE reconciliation_runs ENABLE ROW LEVEL SECURITY;
ALTER TABLE ml_feedback_log ENABLE ROW LEVEL SECURITY;
ALTER TABLE audit_log ENABLE ROW LEVEL SECURITY;

-- 2. Force RLS for all users (even table owners)
ALTER TABLE purchase_register FORCE ROW LEVEL SECURITY;
ALTER TABLE gst_register FORCE ROW LEVEL SECURITY;
ALTER TABLE reconciliation_runs FORCE ROW LEVEL SECURITY;
ALTER TABLE ml_feedback_log FORCE ROW LEVEL SECURITY;
ALTER TABLE audit_log FORCE ROW LEVEL SECURITY;

-- 3. Create generic policies that read the current tenant from a Postgres session variable
-- Application code must run: SET LOCAL recongraph.current_tenant = 'tenant_123';
-- before executing queries.

CREATE POLICY tenant_isolation_purchase ON purchase_register
    AS RESTRICTIVE
    USING (tenant_id = current_setting('recongraph.current_tenant', true));

CREATE POLICY tenant_isolation_gst ON gst_register
    AS RESTRICTIVE
    USING (tenant_id = current_setting('recongraph.current_tenant', true));

CREATE POLICY tenant_isolation_runs ON reconciliation_runs
    AS RESTRICTIVE
    USING (tenant_id = current_setting('recongraph.current_tenant', true));

CREATE POLICY tenant_isolation_feedback ON ml_feedback_log
    AS RESTRICTIVE
    USING (tenant_id = current_setting('recongraph.current_tenant', true));

CREATE POLICY tenant_isolation_audit ON audit_log
    AS RESTRICTIVE
    USING (tenant_id = current_setting('recongraph.current_tenant', true));

-- 4. Create an admin bypass (optional, for migrations or global reporting)
-- A specific `recongraph_admin` role could bypass RLS if explicitly granted BYPASSRLS.
-- ALTER ROLE recongraph_admin BYPASSRLS;
