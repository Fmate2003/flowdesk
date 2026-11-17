# Architecture

Browser → Nginx (frontend, :8080) → Flask API (backend, 3 replicas) → PostgreSQL (database, persistent named volume).

Swarm provides overlay networks (`webnet`, `dbnet`), DNS-based service discovery, load balancing, and task reconciliation. Database credentials are provisioned using a Docker Secret. The PostgreSQL volume resides on the single Swarm host; single-node storage is not multi-host high availability.

The backend initializes the schema on startup using a transaction-scoped advisory lock. `ALTER TABLE ... ADD COLUMN IF NOT EXISTS` preserves older task records.
