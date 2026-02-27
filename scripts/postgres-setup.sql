-- Run this after restarting PostgreSQL (with pg_hba set to trust).
-- Sets postgres password and creates app user + database for .env

-- 1) Set a password for the postgres superuser (change 'postgres' if you want)
ALTER USER postgres WITH PASSWORD 'postgres';

-- 2) Create app user and database to match your .env (user / password / udayatech)
CREATE USER "user" WITH PASSWORD 'password';
CREATE DATABASE udayatech OWNER "user";
GRANT ALL PRIVILEGES ON DATABASE udayatech TO "user";
