# Incident 2 — Marina Bay

Evidence source: `../source-code-findings.md`, `../environment/runtime-checks.txt`, `../environment/diagnostics.sql`.

Verified from assignment alert: three API restarts in 15 minutes; CSM reports intermittent 502 and invoices in Validated since approximately 09:30.

Verified from source/config: API 128 MiB memory and memory+swap limit; SourceCache retains raw file/workbook/invoice objects without eviction in inspected code; submission queue is in memory; startup creates a new queue/cache.

Not verified: OOMKilled, exit code, memory peak, actual 502 series, lost queue items, affected invoice IDs or ASP delivery. OOM is a hypothesis only.
