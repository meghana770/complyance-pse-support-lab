# Incident 4 — Bluepeak / Sahara Medical

Evidence source: `../workbook-audit-output.txt`, `../source-code-findings.md`, `../environment/diagnostics.sql`.

Workbook has 60 data rows grouped into 40 invoices and two buyer participant IDs. ASP mock rate limiter: burst 8, refill 2/s, HTTP 429 + Retry-After. API submitter marks Submitted before sending; 429 has no switch case; retry endpoints accept only Validated/Failed and return 409 for Submitted.

This proves a code-level handling gap, not the actual number accepted or throttled in this particular batch. Reconcile API statuses, ASP sender document list and hospital receipt before any resend.
