# Incident summary

On 2026-04-21 between 14:02 and 14:38 UTC, the orders API returned HTTP
503 for ~12% of requests. Root cause was a connection pool exhaustion in
the database client. Mitigation was a deploy reverting the connection
pool change. We need a postmortem document.
