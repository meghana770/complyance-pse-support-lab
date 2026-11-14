# Source-code inspection evidence (static; not runtime reproduction)

Repository files were inspected in the supplied archive. Line numbers below are from the extracted source at the time of review.

## Incident 1 — upload timeout / duplicate checks
- `web/app/api/[...path]/route.ts:6,21-26,32-52`: the portal proxy applies a 60,000 ms abort timeout; timeout is returned as HTTP 504. Other upstream failures become 502.
- `services/api/internal/importer/importer.go:37-39`: importer creates its own 10-minute context from `context.Background()` rather than inheriting the HTTP request context. This is consistent with processing continuing after the portal proxy aborts, subject to DB/ASP work continuing normally.
- `services/api/internal/importer/importer.go:100-114`: invoice groups are validated in a normal sequential loop; each group's validation iterates its rows.
- `services/api/internal/validate/validate.go:67-71,165-173`: `Validate` iterates every row; `validateRow` performs an ASP participant lookup for each row.
- `services/asp-mock/main.go:39-40`: mock participant lookup latency is 200 ms.
- `samples/oasis-builders-nov-2026.xlsx`: 600 data rows, 8 invoice numbers, 75 rows per invoice, 5 distinct buyer participant IDs. At 200 ms per row lookup, the source path models 600 × 0.2 s = 120 s of lookup latency. This is an estimate from code + workbook, not a measured runtime duration.
- `services/api/internal/store/store.go:296-306`: duplicate check looks for the same seller + invoice number in another import, excluding rejected records. `db/init/001_schema.sql` defines a non-unique index on seller/invoice number, not a uniqueness constraint. Concurrent imports can therefore race; exact outcomes require runtime verification.

## Incident 2 — API restart / stuck queue
- `docker-compose.yml:55-63`: API container memory and memory+swap limits are 128 MiB and restart policy is `unless-stopped`.
- `services/api/main.go:56-61`: four submission workers are started; a new in-memory SourceCache is created at process start.
- `services/api/internal/importer/sources.go:20-42`: SourceCache stores raw upload bytes, parsed workbook and mapped invoices in a map; no eviction/expiry/delete method is present in this file.
- `services/api/internal/importer/importer.go:93-96`: every successful parse stores the raw file, workbook and invoice objects in the cache.
- These are memory-pressure risk factors, not proof of OOM. The alert email reports three restarts in 15 minutes; actual restart reason, memory peak, 502 correlation and stuck invoice IDs require runtime/container logs, Prometheus and DB queries. None were available in this execution environment.

## Incident 3 — BR-CO-15 rounding
- `services/api/internal/pint/pint.go:135-152`: per-line VAT is computed from the supplied 2-decimal line net amount and rounded to 2 decimals.
- `services/api/internal/pint/pint.go:156-185`: total net and VAT are accumulated from rounded line amounts; gross is separately accumulated from `quantity × unit price × (1 + VAT rate)` and rounded only at document total.
- `services/asp-mock/main.go:225-230`: ASP BR-CO-15 compares cents of gross against cents of net plus VAT.
- `evidence/workbook-audit-output.txt` reproduces the code formula against the supplied Al Noor workbook: 6 invoices; 0042, 0044 and 0046 differ from net+VAT by AED 0.01, 0.02 and 0.01 respectively. This is a deterministic source-formula reproduction, not a live ASP response.

## Incident 4 — ASP 429
- `services/asp-mock/main.go:35-37,134-150,274-283`: per-sender token bucket allows burst 8, then replenishes at 2 requests/second; excess returns HTTP 429 and `Retry-After`.
- `services/api/internal/submit/submit.go:114-128`: invoice is moved to Submitted before the ASP call; response is logged.
- `services/api/internal/submit/submit.go:133-155`: switch handles 200, 422, 500, 502, 503 and 504. There is no 429 branch, no retry scheduling and no status transition for 429. Therefore the invoice remains Submitted after a 429 response unless another process changes it.
- `services/api/internal/httpapi/httpapi.go:255-276`: individual retry accepts only Validated or Failed; Submitted returns HTTP 409.
- `services/api/internal/httpapi/httpapi.go:221-234`: batch retry only requeues retryable statuses from the store.
- `samples/sahara-medical-batch-1116.xlsx`: 60 data rows grouped into 40 invoices; one seller and two buyer participant IDs. The 8-document burst capacity is insufficient for 40 simultaneous sends. Runtime accepted/rejected counts and delivery count must be confirmed against ASP list and database; not run here.

## Incident 5 — date validation
- `services/api/internal/sheet/sheet.go:167-185`: ParseDate accepts ISO `YYYY-MM-DD` text or numeric Excel date serials; slash-separated date text is rejected.
- `services/api/internal/validate/validate.go:113-118`: both invoice issue date and payment due date are validated using ParseDate and generate AE-BR-04.
- `samples/ghaf-cafe-nov-2026.xlsx`: 8 data rows / 4 invoice numbers; all 8 issue-date cells and all 8 due-date cells are text strings in slash format. Thus the supplied workbook has two date fields per line affected, not just the issue date mentioned in the email.
- `docs/template-field-guide.md` documents the same requirement and explains converting real Excel dates or text values to ISO format. This is expected product behaviour under current documentation, not a confirmed product defect.
