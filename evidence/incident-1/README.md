# Incident 1 — Oasis Builders

Evidence source: `../workbook-audit-output.txt`, `../source-code-findings.md`, `../environment/runtime-checks.txt`.

Verified from supplied workbook: 600 data rows, eight invoice numbers, 75 rows per invoice, five buyer participant IDs.

Verified from source: 60-second portal proxy timeout; importer has independent 10-minute context; sequential validation; participant lookup per row; ASP mock lookup latency 200 ms; duplicate check queries another import and ignores rejected rows. Estimated lookup path is 120 seconds (not measured in runtime).

Not verified: actual HTTP 504, import IDs, invoice final statuses, duplicate race outcomes and ASP receipt/message IDs. Do not advise resend before reconciliation.
