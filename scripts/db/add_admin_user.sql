BEGIN;

--
-- Register UID as Diablo admin
--
-- USAGE:
--   psql ... -v uid=123456 -f scripts/db/add_admin_user.sql
--

-- Create admin user
INSERT INTO admin_users (uid, created_at, updated_at)
  SELECT :'uid', now(), now()
  WHERE NOT EXISTS (SELECT id FROM admin_users WHERE uid = :'uid');

-- Done

COMMIT;
