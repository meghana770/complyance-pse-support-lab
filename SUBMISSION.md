# Submission

- **Name:** Meghana Bagari
- **Date submitted:** 14/11/2026
- - **Repository link:** https://github.com/meghana770/complyance-pse-support-lab
- **Total time spent (real time):** Approximately 4–6 hours.
> Replies below are drafts written on the **exercise clock** (Monday 16 November 2026, Asia/Dubai, UTC+4). They were not sent. No real customer or company was contacted. Actual investigation activity is kept separate from the exercise clock.

> **Execution and verification status:** The Docker Compose environment was subsequently started successfully. PostgreSQL, API, ASP mock, web portal, Prometheus, Grafana and supporting services were brought up and verified. Four incident scenarios were replayed: Oasis Builders, Al Noor Fuel, Bluepeak/Sahara Medical and Ghaf Tree Café. Runtime logs and database results are saved under `evidence/runtime/`, with baseline screenshots under `evidence/screenshots/`. Oasis original replay completed with eight accepted invoices in 123.7 seconds. A controlled repeat upload timed out at the client after 60 seconds, while the API continued and completed after 121.64 seconds with eight portal rejections. The results are consistent with the duplicate-number guard. Al Noor's BR-CO-15 rejections, Bluepeak/Sahara's HTTP 429 rate limiting, and Ghaf's AE-BR-04 date validation failures were reproduced. Marina Bay's restart/502 symptoms were not independently reproduced, so its runtime root cause remains unconfirmed. See the runtime evidence files for the observed results.

- **Items selected for investigation and why:**
  1. **Incident 2 — Marina Bay:** Provisional P1 due to the reported API restarts, 502 errors and potentially broad customer impact. Runtime symptoms were not independently reproduced; root cause remains unconfirmed.
  2. **Incident 1 — Oasis Builders:** Original replay completed in 123.7 seconds with eight accepted invoices. A controlled repeat upload reproduced the 60-second client timeout while backend processing continued to completion after 121.64 seconds; all eight repeated invoice numbers were rejected by the portal.
  3. **Incident 4 — Bluepeak / Sahara Medical:** Reproduced HTTP 429 rate limiting. Of 40 invoices, 8 were accepted and 32 remained Submitted without ASP references.
  4. **Incident 3 — Al Noor Fuel:** Reproduced BR-CO-15 rejections: three of six invoices were rejected by the ASP.
  5. **Incident 5 — Ghaf Tree Café:** Reproduced AE-BR-04 date-format validation failures; all four invoices were rejected by the portal.

The investigations combine source-code analysis and runtime evidence. Oasis Builders, Al Noor Fuel, Bluepeak/Sahara Medical and Ghaf Tree Café were tested at runtime. Oasis's original upload was accepted; a controlled repeat upload reproduced the long-processing/client-timeout behaviour and portal rejection of all eight repeated invoices. Marina Bay's reported symptoms remain unconfirmed. The evidence level is stated per incident.

---

## Incident 1 â€” `inbox/01-oasis-builders-upload-stuck.md`

### Acknowledgement

- **Sent at (exercise clock):** Monday 16 November 2026, 09:20 Asia/Dubai (draft; within the P2 first-response target of 10:05).
- **Reply:**

> Hi Rashid,
>
> Thank you for explaining what happened. I understand that the same November workbook was uploaded more than once, the portal remained on Processing and you are now seeing duplicate-number messages without knowing which invoices reached the network.
>
> I am checking the import records and invoice-by-invoice delivery status before recommending any further action. Please do not upload the file again or retry individual invoices until I confirm which records already exist; that could create more duplicate records. I will send you a status breakdown and a safe next step by 11:20 UAE time.
>
> Regards,  
> Product Support

### Priority and justification

- **Priority:** P2 â€” major degradation affecting one customer's large month-end batch; invoice delivery is uncertain, but the inbox does not establish a wider production outage.
- **Why:** 600 spreadsheet rows represent eight invoices and the controller needs them for month-end close. The customer cannot safely determine which invoices were sent. Raise to P1 only if checks show that no invoices are reaching the ASP for one or more customers or broader production impact is confirmed.
- **SLA deadlines I am working to:** first response by 10:05; next update by 11:20 (within the 2â€“4 hour P2 cadence); resolution/workaround target 17:05 Monday 16 Nov (8 business hours from 09:05, Dubai business hours 08:00â€“18:00).

### Investigation log

| Sequence | What I checked / did | What I found |
|---|---|---|
| 1 | Read the customer report and inspected `samples/oasis-builders-nov-2026.xlsx`. | Workbook has 600 data rows, eight invoice numbers (`OBS-2611-001` through `OBS-2611-008`), 75 rows per invoice, and five distinct buyer participant IDs. See [workbook audit](evidence/workbook-audit-output.txt). |
| 2 | Traced the portal upload proxy. | `web/app/api/[...path]/route.ts:6,21-26,41-52` sets a 60-second abort timeout and maps a timeout to HTTP 504. |
| 3 | Traced import execution and validation. | `importer.go:37-39` creates a separate 10-minute context from `context.Background()`. `importer.go:100-114` validates invoice groups sequentially. `validate.go:67-71,165-173` checks each row and performs a participant lookup for each row. |
| 4 | Compared lookup behaviour with the ASP mock. | `services/asp-mock/main.go:39-40` sets a simulated participant lookup latency of 200 ms. 600 row-level lookups imply about 120 seconds of lookup latency if all complete serially (600 Ã— 0.2 s); this is a code/workbook estimate, not a measured upload duration. |
| 5 | Inspected duplicate detection and database constraints. | `store.go:296-306` checks another import for the same seller/invoice number, excluding rejected invoices. The schema has a non-unique `(seller_id, invoice_number)` index, not a unique constraint. Concurrent duplicate uploads can race; exact row outcomes require database/runtime inspection. |
| 6 | Replayed the original Oasis workbook using the local Docker Compose stack. | Import `bf68f3c6-2602-4f70-938b-2fdabdf93f81` completed in 123.701 seconds with 8 invoices Accepted. See `evidence/runtime/oasis-replay-result.txt` and `oasis-database-result.txt`. |
| 7 | Created and uploaded a controlled repeat workbook containing the same eight invoice numbers as the accepted import. | The client request timed out after 60 seconds. API logs show import `190b38dd-ba86-4976-a09f-6b598fbaf45a` completed after 121.640 seconds with 8 invoices Rejected and HTTP 201. The import result is saved in `evidence/runtime/oasis-duplicate-test-result.json`. |
| 8 | Reviewed API logs for the repeated upload request. | A second request created import `9810b1d2-7f54-477b-b112-f64d8223e225`, which also completed after approximately 121.311 seconds with 8 rejections. Both requests are recorded in `evidence/runtime/oasis-duplicate-upload-logs.txt`. |
| 9 | Compared runtime results with duplicate validation code. | `services/api/internal/store/store.go:299-307` checks for another non-rejected invoice with the same seller and invoice number. `services/api/internal/validate/validate.go:75-80` reports the duplicate validation rule. The import summary confirms portal rejections, but the detailed rejection messages were not captured in this result. |
**Dead ends / ruled out:** The original replay did not reproduce a failure: all eight invoices were accepted. The controlled repeat upload did reproduce the long-processing behaviour. The client timed out at 60 seconds, but the API continued processing and completed after 121.64 seconds. This demonstrates that a client timeout does not establish that the server cancelled the import. The second upload request is also visible in the API logs. The import summary confirms eight portal rejections; the detailed rejection messages were not captured, so the precise validation message is not asserted here.
### Root cause

- **What happened:** The 600-row workbook takes approximately two minutes to process in this environment. The original replay completed successfully, but the controlled repeat upload exceeded the client's 60-second wait and the client timed out while the API continued processing. The controlled repeat import completed with all eight invoices rejected by the portal.
- **Where:** `web/app/api/[...path]/route.ts:6,21-26,41-52`; `services/api/internal/importer/importer.go:37-39,100-114`; `services/api/internal/validate/validate.go:67-71,75-80,165-173`; `services/asp-mock/main.go:39-40`; `services/api/internal/store/store.go:299-307`.
- **Why it happens:** The workbook has 600 data rows. Validation performs participant lookups and the ASP mock adds 200 ms simulated lookup latency. The original replay took 123.701 seconds; the controlled repeat import took 121.640 seconds. Both exceed the 60-second client/proxy timeout. The importer uses a separate 10-minute context, so the client timeout does not cancel the server-side import. The duplicate guard checks for an existing non-rejected invoice with the same seller and invoice number.
- **Evidence:** [Workbook audit output](evidence/workbook-audit-output.txt), [original replay result](evidence/runtime/oasis-replay-result.txt), [original database result](evidence/runtime/oasis-database-result.txt), [controlled repeat import result](evidence/runtime/oasis-duplicate-test-result.json), [repeat upload API logs](evidence/runtime/oasis-duplicate-upload-logs.txt), and [source-code findings](evidence/source-code-findings.md).
- **Confidence and open questions:** High confidence that processing exceeded the 60-second client timeout and continued server-side, based on measured runtime results and API logs. High confidence that the controlled repeat import ended with eight portal rejections. The duplicate-check source supports the likely reason, but the detailed rejection messages were not captured in the import summary. The second request is also recorded; it should be disclosed as a repeated test request, not presented as a separate customer action.
### Customer resolution reply OR escalation note

- **Which one and why:** Escalation to L3 is appropriate because the likely issue is in the product's synchronous upload path and duplicate handling. L1 retains customer ownership.

#### Escalation: Large upload exceeds portal timeout; repeated upload creates duplicate ambiguity

**Priority:** P2 â€” eight month-end invoices in one 600-row workbook; customer cannot identify which invoices were delivered.

**Customer / seller:** Oasis Builders Supply LLC; seeded seller ID 2; Peppol sender `0235:1003182746`.

**Reported by / at:** Rashid Al Mansoori, customer email, 16 Nov 2026 09:05 Dubai.

**Affected:** November workbook, 600 rows, eight invoice numbers. Original accepted import: `bf68f3c6-2602-4f70-938b-2fdabdf93f81`. Controlled repeat import: `190b38dd-ba86-4976-a09f-6b598fbaf45a` (8 portal rejections). A second repeat request is recorded as `9810b1d2-7f54-477b-b112-f64d8223e225`.

**Symptoms (customer view):** Upload remains Processing, later returns an error; subsequent attempts show â€œalready existsâ€; customer does not know which invoices reached the ASP.

**Evidence:**
- Workbook: 600 rows / eight invoice numbers / 75 rows per invoice; see `evidence/workbook-audit-output.txt`.
- Portal proxy: 60-second abort and 504 mapping at `web/app/api/[...path]/route.ts:6,21-26,41-52`.
- Importer: independent 10-minute context and sequential invoice validation at `importer.go:37-39,100-114`.
- Directory lookup: each row invokes lookup at `validate.go:67-71,165-173`; mock latency 200 ms at `asp-mock/main.go:39-40`.
- Database: duplicate query is `store.go:296-306`; schema index is non-unique. Live SQL output unavailable; see `evidence/environment/diagnostics.sql` (NOT EXECUTED).
- ASP response/log/metric evidence: unavailable because runtime stack could not be started.

**Steps to reproduce:**
1. Upload the supplied 600-row Oasis workbook using seller ID 2.
2. Observe elapsed time and portal proxy status.
3. Without re-uploading, query import and invoice status records and list ASP documents for sender `0235:1003182746`.
4. In a disposable test environment only, repeat the same upload to test duplicate detection and race behaviour.

**What I have already tried / ruled out:** Inspected workbook shape, source timeout, validation loop, directory latency and duplicate query. Did not run an upload or destructive reset. Workbook shape is valid at a structural level; runtime validation has not been proven.

**Suspected cause (with confidence):** Portal timeout at 60 seconds while importer continues under its own 10-minute context; repeat uploads cause cross-import duplicate checks. Confidence high for timeout path, medium for duplicate race; runtime evidence outstanding.

**Workaround in place:** No safe resend advised. First reconcile each invoice's database status and ASP reference. Do not retry or upload again until reconciliation is complete.

**Timeline:** 09:05 report received; 09:20 acknowledgement draft; investigation steps documented above; 11:20 customer update due.

**Ask:** Engineering to make large-file import asynchronous or increase/stream the proxy contract safely; deduplicate participant lookups by buyer participant ID within an import; make upload idempotent by seller + invoice number/import key; add concurrency-safe uniqueness/idempotency handling and a visible import ID/status endpoint. Provide a safe reconciliation procedure for the eight invoices.

**Next customer update due:** 11:20 Dubai time.

**Customer update draft:**

> Rashid, I have identified a likely reason for the error: this workbook requires many participant checks, while the portal stops waiting after 60 seconds. That timeout does not tell us whether the API finished processing. I am reconciling the eight invoice records against the ASP references before advising any resend. Please keep the file unchanged and do not upload it again. I will send the invoice-by-invoice result by 11:20 UAE time.

### Workaround offered

Do not upload the workbook again or use batch retry while status is uncertain. Reconcile the eight invoice numbers against `invoices` (status, import ID, ASP message ID) and the ASP `GET /v1/documents?sender=0235:1003182746` list. Only invoices confirmed absent from the ASP and eligible for retry should be reprocessed under support/engineering guidance.

### Prevention ideas

- Make import acceptance asynchronous and return a durable import ID immediately; expose progress separately.
- Avoid one participant lookup per row; cache/deduplicate lookups per distinct buyer participant ID with bounded TTL.
- Add idempotency keys and a concurrency-safe uniqueness rule for seller + invoice number.
- Surface â€œrequest timed out; processing may continueâ€ with an import status link rather than inviting blind retries.
- Add regression tests for two concurrent uploads of the same invoice numbers.

---

## Incident 2 â€” `inbox/02-alert-api-restarted-marina-bay.md`

### Acknowledgement

- **Sent at (exercise clock):** Monday 16 November 2026, 10:00 Asia/Dubai (18 minutes after 09:42 alert; within P1 15â€“30 minute response window).
- **Sent to:** Priya Nair / support on-call thread; internal acknowledgement draft. A customer-facing message should be sent by the account owner once affected Marina Bay scope is confirmed.
- **Reply:**

> Priya, I am taking ownership of this as a P1 pending impact confirmation. The alert reports three API restarts in 15 minutes, and your update describes intermittent 502s across customers and invoices remaining in Validated. I am escalating to the engineering on-call now while checking restart reasons, memory, queue recovery and affected invoice statuses. Please do not promise Marina Bay that Wednesday's go-live is safe until we have verified recovery and completed a controlled end-to-end submission check. I will update you by 10:30 UAE time, even if the investigation is still in progress.

### Priority and justification

- **Priority:** P1 â€” provisional, based on a critical production restart alert plus reports of intermittent 502s affecting multiple customers and invoices not progressing to the ASP.
- **Why:** P1 applies when production is down or invoices are not reaching the ASP for one or more customers. The available email suggests multi-customer service degradation and stuck invoices; scope and actual delivery impact must be confirmed immediately. If evidence shows only a small subset and the service remains broadly operational, reclassify to P2 and notify stakeholders.
- **SLA deadlines I am working to:** first response 09:57â€“10:12 (draft at 10:00); updates every 30â€“60 minutes (next 10:30); P1 resolution target 13:42 (4 hours from 09:42 alert; target, not a promise).

### Investigation log

| Sequence | What I checked / did | What I found |
|---|---|---|
| 1 | Read the internal Grafana alert and CSM forward. | Alert states three API restarts in 15 minutes; CSM reports intermittent 502s and invoices in Validated since approximately 09:30. These are reported symptoms, not independently queried metrics. |
| 2 | Inspected API resource limits and restart policy. | `docker-compose.yml:55-63` configures 128 MiB memory and memory+swap, with `restart: unless-stopped`. |
| 3 | Inspected API startup and in-memory submission queue. | `main.go:56-61` starts four workers and constructs a fresh SourceCache at startup. Submitter queue is an in-memory channel (`submit.go:55-74`); no durable queue is visible in the inspected path. |
| 4 | Inspected source cache lifecycle. | `sources.go:20-42` stores raw upload bytes, workbook and invoice objects in a map; no expiry/eviction is implemented in this file. `importer.go:93-96` stores each successful import. |
| 5 | Started Docker Compose and checked runtime health, logs, resources and monitoring. | API and ASP health endpoints returned HTTP 200. API memory limit was 128 MiB. Baseline logs, container resources and Prometheus targets were captured. No Marina Bay-specific restart or 502 event was independently reproduced. |

**Dead ends / ruled out:** The local Docker Compose stack started successfully. API and ASP health checks returned HTTP 200. Baseline container resources, API logs and Prometheus targets were captured. These checks establish that the local environment was operational; they do not reproduce the reported three restarts, customer-facing 502s or invoices stuck in Validated. No specific restart cause or memory-related failure was confirmed.

### Root cause

- **What happened:** The customer-facing report describes three API restarts in 15 minutes, intermittent HTTP 502 responses and invoices remaining in Validated. These symptoms were not independently reproduced during the local runtime investigation.
- **Where:** Relevant investigation points are `docker-compose.yml:55-63` (API memory and restart configuration), API startup and worker initialization (`main.go:56-61`), the in-memory submission queue (`submit.go:55-74`), and source-cache lifecycle (`sources.go:20-42`).
- **Why it happens:** A constrained API memory limit, loss of in-memory queue state during a process restart, or retained source-cache objects are plausible investigation leads. They are not established causes. The local baseline checks do not demonstrate an out-of-memory kill, queue loss or a restart loop.
- **Evidence:** `evidence/runtime/api-health.txt`, `evidence/runtime/asp-health.txt`, `evidence/runtime/api-asp-baseline-logs.txt`, `evidence/runtime/api-memory-limit.txt`, `evidence/runtime/container-resources.txt`, `evidence/runtime/prometheus-targets.json`, and `evidence/runtime/full-stack-baseline-logs.txt`.
- **Confidence and open questions:** The reported symptoms are supported by the incident report, but the runtime root cause remains unconfirmed. Obtain the affected production time window, restart reason and exit code, memory/OOM metrics, API logs around each restart, 502 traces, and database status history for the affected invoices. Escalate to on-call engineering immediately for the reported P1 impact; do not wait for root-cause confirmation.
### Customer resolution reply OR escalation note

- **Which one and why:** Immediate L3/on-call escalation is required for a P1. Do not wait for a complete root cause. L1 retains customer and CSM updates.

#### Escalation: API restart alert with intermittent 502s and invoices stuck in Validated

**Priority:** P1 provisional â€” multiple customers report intermittent upload 502s and stalled invoices; critical alert reports three restarts in 15 minutes.

**Customer / seller:** Marina Bay Hospitality LLC (seed seller ID 3; Peppol ID `0235:1004271935`); additional affected customers not yet identified.

**Reported by / at:** Grafana alert at 09:42 Dubai, forwarded by Priya Nair at 09:50 on 16 Nov 2026.

**Affected:** Invoice IDs/import IDs and exact customer count not yet available; reports of Validated invoices since ~09:30.

**Symptoms (customer view):** Intermittent 502 Bad Gateway during portal uploads; invoices remain Validated rather than progressing to Submitted/Accepted.

**Evidence:**
- Alert payload: `restarts=3` in the preceding 15 minutes (from inbox item; not independently queried).
- Resource policy: API memory and memory+swap cap 128 MiB (`docker-compose.yml:55-63`).
- Cache: no eviction in inspected SourceCache (`sources.go:20-42`).
- Queue: in-memory channel and four workers (`submit.go:55-90`); API startup creates a new queue and cache (`main.go:56-61`).
- Runtime logs, restart exit codes, memory graphs, Prometheus 5xx and database status results: unavailable in current environment.

**Steps to reproduce / investigate:**
1. Inspect `docker inspect` restart count, `State.OOMKilled`, exit code and restart timestamps.
2. Query cAdvisor memory working set against the 128 MiB limit and correlate with restart times.
3. Query Prometheus API request count/5xx and submission queue depth around 09:30â€“09:50.
4. Search Loki for API startup, OOM/termination, database disconnect and submission errors.
5. Query invoice statuses/events for Marina Bay and other sellers; compare ASP message IDs and ASP sender document list.
6. Restart only in a disposable copy after capturing baseline; do not reset production-like assignment data.

**What I have already tried / ruled out:** Static inspection of memory cap, source cache and queue. No runtime restart cause has been confirmed. Do not label this OOM without container evidence.

**Suspected cause (with confidence):** Potential memory pressure from unbounded source cache under a 128 MiB limit; potential loss of queued work on restart. Both are architectural hypotheses, not confirmed causes of this alert.

**Workaround in place:** Keep new large uploads paused for affected sellers until API health is stable. For invoices still Validated, use retry only after confirming they have not already been accepted by the ASP. Do not retry Submitted invoices or promise Wednesday go-live readiness.

**Timeline:** 09:42 alert; 09:50 CSM forward; 10:00 acknowledgement and L3 page draft; next update 10:30.

**Ask:** On-call engineering to confirm restart cause and scope, restore API stability, identify stranded Validated/Submitted invoices, reconcile each against ASP receipt records, and provide a recovery plan. Add startup recovery for safe retryable work and durable queue/outbox semantics. Confirm go-live readiness only after sustained health and end-to-end tests.

**Next customer update due:** 10:30 Dubai time; continue every 30â€“60 minutes while P1.

### Workaround offered

No broad resend. Pause large/bulk uploads while restart cause is being checked. For each affected invoice, compare its persisted status and ASP reference with the ASP's sender document list. Retry only invoices confirmed as Validated/Failed and not already received by the ASP. Submitted records require reconciliation/engineering because the retry API rejects that status.

### Prevention ideas

- Bound SourceCache by TTL/size and release workbook/raw bytes after their retention requirement ends; consider durable object storage.
- Persist submission work in an outbox/queue and reconcile `Validated`/`Submitted` records at startup.
- Alert on memory as a percentage of the cgroup limit, restart reason/OOMKilled and growing cache/queue depth.
- Add a restart recovery test and a controlled end-to-end invoice acceptance test to go-live criteria.

---

## Incident 3 â€” `inbox/03-al-noor-fuel-br-co-15.md`

### Acknowledgement

- **Sent at (exercise clock):** Monday 16 November 2026, 10:30 Asia/Dubai (within P2 first-response target of 11:15).
- **Reply:**

> Dear Fatima,
>
> Thank you for sending the workbook and the BR-CO-15 details. I understand that the auditor needs a clear explanation and that other invoices from the same file were accepted. I am comparing the invoice totals generated by our system with the line amounts in your file and will provide an invoice-by-invoice explanation. Please do not change the source quantities or prices at this stage. I will update you by 12:30 UAE time with the findings and the safest next step.
>
> Kind regards,  
> Product Support

### Priority and justification

- **Priority:** P2 â€” a subset of six fuel invoices is reportedly rejected and the issue affects a VAT/audit review; evidence points to a product calculation defect.
- **Why:** Three invoices in the supplied workbook produce a BR-CO-15 mismatch under the source formula; the customer's source line values should not be altered to compensate for a platform calculation inconsistency.
- **SLA deadlines I am working to:** first response by 11:15; next update by 12:30; P2 resolution target Tuesday 17 Nov 08:15 (8 business hours from 10:15 Monday; 7h45 Monday plus 15 minutes Tuesday after the 18:00 close).

### Investigation log

### Investigation log

| Sequence | What I checked / did | What I found |
|---|---|---|
| 1 | Inspected the supplied Al Noor workbook and grouped rows by invoice number. | 13 data rows form six invoices: 0041–0046. |
| 2 | Inspected the PINT total calculation. | Per-line VAT is rounded from supplied line net amounts (`pint.go:135-152`); gross total is calculated separately from quantity × unit price (`pint.go:156-185`). |
| 3 | Reproduced the source calculation against workbook values. | 0042, 0044 and 0046 showed gross-total mismatches. |
| 4 | Replayed the Al Noor scenario using Docker Compose. | HTTP 201 in 3.4 seconds; import ID `827ec13c-4358-4ffb-a2ba-581bfc9c44df`; six invoices processed. |
| 5 | Queried invoice results in PostgreSQL. | Three invoices were Accepted and three Rejected. The rejected invoices included BR-CO-15 differences of AED 0.01 and AED 0.02. |
| 6 | Compared the runtime result with the ASP validation code. | `asp-mock/main.go:225-230` compares the inclusive amount against exclusive amount plus VAT. The runtime rejections match the rounding discrepancy identified in the source calculation. |

**Dead ends / ruled out:** The ASP was reachable and the import completed; this was not a general ASP outage. Three of six invoices were accepted, while three were rejected by BR-CO-15. The discrepancies were small (AED 0.01–0.02), so changing customer prices or quantities would not be an appropriate workaround. The runtime results align with the calculation inconsistency found in the API source.

### Root cause

- **What happened:** The API calculates VAT at line level and rounds each line before aggregating totals. Its tax-inclusive amount is calculated separately. For some multi-line invoices, these calculation paths produce a one- or two-fils difference. The ASP's BR-CO-15 validation rejects the inconsistent totals.
- **Where:** `services/api/internal/pint/pint.go:135-152,156-185`; `services/asp-mock/main.go:215-230`.
- **Why it happens:** Independently rounding line-level VAT and calculating the inclusive total through a separate expression can produce different results when multiple lines are aggregated. Runtime testing showed three invoices rejected with differences of AED 0.01–0.02.
- **Evidence:** `evidence/runtime/al-noor-replay-result.txt`, `evidence/runtime/al-noor-invoice-results.txt`, `evidence/runtime/al-noor-original-import-result.json`, and `evidence/runtime/al-noor-rounding-analysis.txt`.
- **Confidence and open questions:** High confidence in the rounding inconsistency: the source calculation and runtime BR-CO-15 rejections agree. A code correction should calculate totals consistently using the applicable PINT AE rounding rules, followed by regression tests for single-line and multi-line invoices. No production fix was applied during this investigation.


- **Which one and why:** Escalate to L3 because the source calculation appears inconsistent with the ASP's arithmetic rule. The customer's original quantities/prices should not be changed to hide a product defect. L1 owns the auditor-facing update.

#### Escalation:

#### Escalation: PINT BR-CO-15 total mismatch in Al Noor invoices

**Priority:** P2 — three of six invoices were rejected, creating VAT and audit risk.

**Customer / seller:** Al Noor Fuel & Lubricants LLC; seeded seller ID 4; sender `0235:1005362841`.

**Reported by / at:** Fatima Khoury, customer email, 16 Nov 2026 10:15 Dubai.

**Affected:** Import `827ec13c-4358-4ffb-a2ba-581bfc9c44df`; six invoices processed, three Accepted and three Rejected. The rejected invoice records contain BR-CO-15 calculation errors.

**Symptoms:** The upload returned HTTP 201, but the ASP rejected three invoices while the other three were accepted.

**Evidence:**
- Replay: `evidence/runtime/al-noor-replay-logs.txt` — HTTP 201 in 3.4 seconds.
- Database results: `evidence/runtime/al-noor-invoice-results.txt`.
- Replay summary: `evidence/runtime/al-noor-replay-result.txt`.
- Calculation source: `services/api/internal/pint/pint.go:135-152,156-185`.
- ASP validation: `services/asp-mock/main.go:225-230`.

**Steps to reproduce:**
1. Replay the Al Noor workbook using the tools load generator.
2. Capture the import ID and query all invoices belonging to it.
3. Compare inclusive totals against exclusive totals plus VAT.
4. Inspect the ASP rejection messages for BR-CO-15.

**What I have already tried / ruled out:** Confirmed that the upload itself succeeded. The database shows three Accepted and three Rejected invoices. The rejection messages identify BR-CO-15 discrepancies. The source calculation provides a matching explanation for the rounding differences.

**Root cause assessment:** High confidence that inconsistent rounding in `pint.computeTotals` causes the reproduced BR-CO-15 failures. Engineering and Finance must confirm the canonical PINT AE rounding policy before changing the calculation.

**Workaround in place:** Preserve the original workbook and rejected invoice records. Do not change customer quantities or prices to bypass validation. Do not blindly resend accepted invoices. Engineering should confirm the corrected calculation and controlled reissue process.

**Timeline:** 10:15 report received; 10:30 acknowledgement draft; runtime replay and database investigation completed during the lab session. The customer update remains due at 12:30 Dubai time on the exercise clock.

**Ask:** Engineering to align gross calculation with rounded invoice line extensions and VAT totals using decimal-safe arithmetic, add regression tests for fractional unit prices and rounding boundaries, and confirm a controlled correction/reissue procedure.

**Next customer update due:** 12:30 Dubai time.

**Customer update draft:**

> Fatima, we successfully reproduced the issue. The six-invoice upload completed, but three invoices were rejected by the ASP with BR-CO-15 total-calculation errors. Our investigation points to a rounding inconsistency in how gross, net and VAT amounts are calculated. We have escalated this to engineering and are seeking confirmation of the compliant correction before advising any reissue. Please retain the original workbook and do not alter your source prices. I will update you by 12:30 UAE time.

### Workaround offered

No unapproved manual edits to the customer's source workbook. Preserve the original data and rejected invoice numbers. After engineering confirms the corrected calculation, regenerate only the affected payloads/invoices and verify the ASP acceptance and message IDs. Any manual adjustment must be approved by the customer's finance owner and documented for the auditor.

### Prevention ideas

- Use decimal arithmetic or integer minor units rather than binary float for monetary totals.
- Derive invoice gross from the same rounded net + VAT amounts that are sent in the payload.
- Add regression tests for 3-decimal unit prices, half-fils extensions and multiple lines/categories.
- Validate BR-CO-15 locally before sending to ASP and expose the exact computed components to support.

---

## Incident 4 â€” `inbox/04-bluepeak-sahara-not-received.md`

### Acknowledgement

- **Sent at (exercise clock):** Monday 16 November 2026, 11:45 Asia/Dubai (within P2 first-response target of 12:30).
- **Reply:**

> Hi Daniel,
>
> Thanks for the details. I understand the connector received HTTP 201 and the portal shows Submitted, but Emirates Palm Hospital has received only part of the batch and many ASP references are blank. Please do not resend the 40-invoice batch yet; an import acknowledgement is not the same as confirmation that every invoice was accepted by the ASP. I am checking the submission and rate-limit handling and will update you by 14:00 UAE time with a safe reconciliation plan.
>
> Regards,  
> Product Support

### Priority and justification

- **Priority:** P2 â€” a subset of a 40-invoice batch appears not to have reached the buyer, creating a payment-run risk; the report does not establish that all customers or all invoices are unable to submit.
- **Why:** HTTP 201 acknowledges the import endpoint, not each background ASP delivery. Empty ASP references and partial buyer receipt require invoice-by-invoice reconciliation. Raise to P1 if the evidence shows no invoices are reaching the ASP for a broader customer scope.
- **SLA deadlines I am working to:** first response by 12:30; next update by 14:00; P2 resolution target Tuesday 17 Nov 09:30 (8 business hours from 11:30 Monday: 6h30 Monday + 1h30 Tuesday).

### Investigation log

### Investigation log

| Sequence | What I checked / did | What I found |
|---|---|---|
| 1 | Audited `samples/sahara-medical-batch-1116.xlsx`. | 60 data rows group into 40 invoices (`SMS-1116-001`–`SMS-1116-040`) for two buyer participant IDs. |
| 2 | Inspected the ASP mock rate limiter. | `asp-mock/main.go:35-37,134-150,274-283` defines a per-sender burst of eight followed by two requests per second; excess requests receive HTTP 429 and `Retry-After`. |
| 3 | Inspected the API submission flow. | `submit.go:114-155` marks invoices Submitted before the ASP response and does not handle HTTP 429 as a retryable outcome. |
| 4 | Replayed the Sahara scenario using Docker Compose. | HTTP 201 in 15.5 seconds; import ID `947ac9ae-f137-4f0b-a96f-23b1bd352355`; 40 invoices processed. |
| 5 | Inspected API and ASP logs. | Repeated HTTP 429 rate-limit responses were recorded for sender `0235:1006453719`. |
| 6 | Queried invoice records for the import. | Eight invoices were Accepted. Thirty-two remained Submitted without ASP message references. |
| 7 | Compared runtime behaviour with retry handling. | `httpapi.go:255-276` only permits retry for Validated or Failed invoices. Submitted records are not eligible for the normal retry endpoint. |

**Dead ends / ruled out:** The ASP was reachable and accepted eight invoices, so this was not a complete ASP outage. The remaining 32 invoices were left in Submitted without ASP message references. The retry endpoint was tested against one affected invoice and returned HTTP 409 because its current status was Submitted. This confirms that the normal retry path cannot recover these records in their current state.

### Root cause

- **What happened:** The batch contained 40 invoices. Eight were accepted by the ASP, while repeated HTTP 429 responses left 32 invoices in Submitted without ASP message references. The import itself returned HTTP 201, but that response did not mean all invoices had been delivered successfully.
- **Where:** `services/asp-mock/main.go:35-37,134-150,274-283`; `services/api/internal/submit/submit.go:114-155`; `services/api/internal/httpapi/httpapi.go:255-276`; `services/api/internal/httpapi/httpapi.go:157-163`; `services/api/internal/importer/importer.go:125-126`.
- **Why it happens:** The ASP mock applies a per-sender rate limit with a burst of eight followed by two requests per second. The API marks invoices Submitted before receiving the ASP response and does not handle HTTP 429 as a retryable outcome. The normal retry endpoint only permits Validated or Failed invoices, leaving Submitted records ineligible for retry.
- **Evidence:** `evidence/runtime/bluepeak-replay-logs.txt`, `evidence/runtime/bluepeak-invoice-results.txt`, and `evidence/runtime/bluepeak-retry-test.txt`. The retry test records HTTP 409 for an affected Submitted invoice.
- **Confidence and open questions:** High confidence that rate limiting occurred and that 32 invoices remained in Submitted without ASP references. High confidence that the normal retry endpoint rejects this state, based on the runtime HTTP 409 test and source code. The receiving ASP's records must still be reconciled before any invoice is resent, to avoid duplicate delivery.
### Customer resolution reply OR escalation note

- **Which one and why:** Escalate to L3 because this is an integration/state-machine defect. L1 retains communication with Daniel and Sahara's AR team.

#### Escalation:

#### Escalation: ASP HTTP 429 leaves 32 invoices Submitted without ASP references

**Priority:** P2 — 40-invoice batch with 32 records lacking ASP references and potential payment-run impact.

**Customer / seller:** Sahara Medical Supplies FZE; seeded seller ID 5; sender `0235:1006453719`.

**Reported by / at:** Daniel Okafor, Bluepeak ERP Integrations, 16 Nov 2026 11:30 Dubai.

**Affected:** Import `947ac9ae-f137-4f0b-a96f-23b1bd352355`; 40 invoices processed, eight Accepted and 32 left Submitted without ASP references.

**Symptoms:** Connector receives HTTP 201, while downstream submission is incomplete. ASP logs show HTTP 429 rate limiting.

**Evidence:**
- Replay: `evidence/runtime/bluepeak-replay-logs.txt` — HTTP 201 in 15.5 seconds.
- Database results: `evidence/runtime/bluepeak-invoice-results.txt`.
- API/ASP logs: captured terminal output showing HTTP 429 responses and rate-limit warnings.
- ASP limiter: burst eight followed by two per second (`asp-mock/main.go:35-37,274-283`).
- API submitter: `submit.go:114-155`.
- Retry guard: `httpapi.go:255-276`.

**Steps to reproduce:**
1. Replay the 40-invoice Sahara workbook.
2. Capture the import ID and API/ASP logs.
3. Query all invoice records belonging to the import.
4. Compare status and ASP message IDs with the ASP sender document list.
5. Verify that HTTP 429 responses do not create durable retry work.

**What I have already tried / ruled out:** The upload endpoint returned HTTP 201, but this did not guarantee downstream delivery. Runtime logs confirmed rate limiting. Database results confirmed eight Accepted and 32 Submitted without ASP references.

**Root cause assessment:** High confidence that unhandled HTTP 429 responses and the missing retry-state transition caused the observed incomplete submission state. Actual buyer-side receipt remains to be reconciled.

**Workaround in place:** Do not resend the full batch. Reconcile all 40 invoice numbers against API and ASP records. Engineering should safely move confirmed never-received records into a retryable state before paced resubmission.

**Timeline:** 11:30 report received; 11:45 acknowledgement draft; runtime replay and database/log investigation completed during the lab session. The next customer update remains due at 14:00 Dubai time on the exercise clock.

**Ask:** Engineering to handle 429 as a retryable outcome, honour `Retry-After` with bounded exponential backoff and jitter, persist retry state and attempts, record invoice events, and provide a safe reconciliation/requeue operation.

**Next customer update due:** 14:00 Dubai time.

**Customer update draft:**

> Daniel, we reproduced the partial-submission behaviour. The 40-invoice import was acknowledged, but only eight invoices reached Accepted status. The remaining 32 are still Submitted without ASP references, and the ASP logs show HTTP 429 rate limiting. We are escalating the retry-handling gap and will reconcile the affected invoice numbers before recommending any resend. Please continue holding the batch. I will provide the next update by 14:00 UAE time.

### Workaround offered

Do not resend the full batch from the ERP connector. Export the 40 invoice numbers and reconcile each against API status, ASP message ID and ASP sender document list. The 32/8 split must not be assumed until confirmed. Engineering must move confirmed never-received records into a safe retryable state; then resubmit only those records at no more than the ASP's allowed rate (burst eight, then two per second) until the permanent retry logic is fixed.

### Prevention ideas

- Add explicit 429 handling and honour `Retry-After` with bounded backoff/jitter.
- Persist a durable submission state and retry count; distinguish `Submitted`, `Accepted`, `Rejected` and `Retry pending` accurately.
- Do not mark a document Submitted until handoff semantics are defined; retain raw ASP response and event for every outcome.
- Add metrics/alerts for 429 count, invoices without ASP reference, age in Submitted, retry queue depth and delivery success ratio.
- Add an integration test for 40 documents against the 8-burst/2-per-second limiter.

---

## Incident 5 â€” `inbox/05-ghaf-cafe-date-error.md`

### Acknowledgement

- **Sent at (exercise clock):** Monday 16 November 2026, 12:25 Asia/Dubai (well within the P4 first-response target of Tuesday 17 Nov 12:10).
- **Reply:**

> Hello Hessa,
>
> I am sorry this has been frustrating, especially when you are trying to issue invoices for your customers. I checked the supplied workbook format: the portal accepts dates entered as `YYYY-MM-DD` or stored as real Excel date cells, but the dates in your file are text written with slashes. The same check applies to both the invoice issue date and payment due date. I will send you simple correction steps now; you do not need to change your invoice numbers or prices. I will check back with you by 15:00 UAE time if you need help.
>
> Kind regards,  
> Product Support

### Priority and justification

- **Priority:** P4 â€” the portal is behaving according to the published template guide; this is a how-to/template-format question affecting one customer and has a straightforward workaround.
- **Why:** The supplied workbook contains four invoice numbers and text-formatted slash dates in both mandatory date columns. The documentation explicitly rejects slash-separated text to avoid ambiguous tax dates. Do not escalate as a product defect. Suggest improving the error message separately.
- **SLA deadlines I am working to:** first response by Tuesday 17 Nov 12:10 (one business day); acknowledgement draft 12:25 Monday; update as agreed (15:00 Monday); resolution target 5â€“10 business days (approximately 23â€“30 Nov, assuming business days and no holidays).

### Investigation log

### Investigation log

| Sequence | What I checked / did | What I found |
|---|---|---|
| 1 | Inspected the supplied Ghaf workbook. | Eight data rows form four invoices (`GTC-118` to `GTC-121`). Both mandatory date columns contain slash-formatted text dates. |
| 2 | Inspected the date parser and validator. | `sheet.ParseDate` accepts ISO dates or numeric Excel date serials. `validate.go:113-119` applies this check to issue and due dates. |
| 3 | Replayed the Ghaf scenario using Docker Compose. | HTTP 201 in 2.2 seconds; import ID `c26039e8-a3bf-4da6-883d-4cd7e5c70cfd`; four invoices processed. |
| 4 | Queried invoice records in PostgreSQL. | All four invoices were Rejected by the portal with AE-BR-04 errors for issue dates and payment due dates. |
| 5 | Compared runtime errors with validator source. | The runtime messages explicitly require `YYYY-MM-DD` and identify values such as `13/11/2026` and `13/12/2026`. |

**Dead ends / ruled out:** The original workbook was readable and contained four invoices. The failure was not caused by a missing worksheet or an unreadable workbook. All four original invoices were rejected because the date strings did not match the parser's accepted format. A separate corrected workbook was then uploaded successfully, confirming the date-format workaround end to end.

### Root cause

- **What happened:** All four original Ghaf invoices were rejected by portal validation with `AE-BR-04`. The workbook supplied dates in `DD/MM/YYYY` format, while the parser accepts ISO `YYYY-MM-DD` date strings or numeric Excel serial dates. A corrected copy converted 16 date cells to ISO format. The subsequent import validated all four invoices and all four were accepted by the ASP.
- **Where:** `services/api/internal/validate/validate.go:113-119`, where invoice dates are parsed using the sheet date parser. The parser supports ISO date strings and numeric Excel serials.
- **Why it happens:** The supplied date strings use a day-first format that the parser does not recognize. The validation failure occurs before ASP submission. Converting the date cells to the accepted ISO format resolves the input validation issue.
- **Evidence:** `evidence/runtime/ghaf-replay-logs.txt`, `evidence/runtime/ghaf-invoice-results.txt`, `evidence/runtime/ghaf-validation-code.txt`, and `evidence/runtime/ghaf-corrected-import-result.json`. The corrected import ID is `d8ffe240-65c5-461e-b596-238a143a7aab`.
- **Confidence and open questions:** High confidence. The original rejection and corrected end-to-end acceptance were both reproduced. The corrected workbook is a workaround; a product improvement would be clearer date-format guidance or explicit support for the expected customer date format, with unambiguous locale handling.
### Customer resolution reply OR escalation note

- **Which one and why:** Customer resolution, not escalation. The product is working as documented; support should help the customer convert the date cells and propose a clearer error message as a product improvement.

> Hello Hessa,
>
> I checked the workbook you sent. The issue is not that 13 November is an invalid date; it is that Excel has stored the value `13/11/2026` as text. To avoid guessing between date conventions, the portal accepts ISO dates such as `2026-11-13` or actual Excel date cells. Please correct both **Invoice issue date** and **Payment due date** columns:
>
> 1. If Excel recognises the cells as dates, select both date columns, choose **Format Cells â†’ Custom**, and enter `yyyy-mm-dd`.
> 2. If the cells are text, convert them to ISO text (for example `2026-11-13`) using the helper-column method in the template guide, then copy and paste as values.
>
> Please check all four invoice numbers before uploading the corrected workbook. Rejected invoice numbers are not consumed, so you can use the same numbers for corrected invoices. Please reply if Excel does not convert the cells as expected; I can guide you through it. I will check back by 15:00 UAE time.
>
> Kind regards,  
> Product Support

### Workaround offered

Convert both mandatory date columns to real Excel dates formatted as `yyyy-mm-dd`, or convert the text values to ISO `YYYY-MM-DD` and paste as values. Keep the actual intended dates unchanged. The supplied guide gives this helper formula for text values: `=TEXT(DATE(RIGHT(A2,4),MID(A2,4,2),LEFT(A2,2)),"yyyy-mm-dd")`. Upload the corrected workbook only after checking both date columns. The status guide states rejected invoices do not consume their invoice numbers.

### Prevention ideas

- Improve AE-BR-04 to say that both issue date and payment due date must be ISO text or real Excel dates, and explain how to convert text.
- Add a template preflight check that identifies text-formatted date cells before upload.
- Add an example workbook with valid real Excel dates and ISO text dates.

---

## Overall

### Prioritisation

1. **Marina Bay (P1 provisional):** internal critical restart alert and possible multi-customer impact; page L3 immediately and establish blast radius.
2. **Oasis Builders (P2):** month-end close and unknown delivery state; prevent unsafe re-upload while reconciling invoices.
3. **Bluepeak / Sahara Medical (P2):** 40-invoice batch with partial delivery/payment-run impact; stop blind resend and reconcile with ASP.
4. **Al Noor Fuel (P2):** tax/audit impact and likely product calculation defect; preserve customer data and escalate.
5. **Ghaf Tree CafÃ© (P4):** expected validation behaviour with a clear self-service workaround; respond kindly without consuming engineering capacity.

The order is impact-based rather than strictly inbox order. Priority 2 items remain P2 unless runtime evidence widens impact to no invoices reaching the ASP across customers, in which case they must be raised to P1.

### What I would do differently

- Establish an import ID and record the original file hash before any repeat upload; never treat a browser timeout as proof of server cancellation.
- Start by capturing a clean baseline, then reproduce one customer at a time. Avoid parallel load runs that make causality unclear.
- Capture exact invoice IDs, status history, ASP message IDs and the ASP sender document list before retrying.
- For the P1 restart alert, page engineering based on confirmed impact while continuing the technical investigation; do not wait for a complete root cause.
- Use a reproducible, isolated test for the VAT rounding edge cases and rate-limit handling.
- Keep the two clocks separate and record real investigation time as it occurs.

### What I learned / what I would need to learn

- **HTTP proxy timeouts versus backend cancellation:** a browser-facing 504 can coexist with a continuing backend task when the task uses an independent context. I would study request cancellation propagation and asynchronous job patterns.
- **Idempotency and concurrency:** checking duplicates is not equivalent to enforcing uniqueness under concurrent uploads. I would study idempotency keys, transactional uniqueness and race-condition tests.
- **Money and rounding:** monetary calculations should use decimal/integer minor-unit arithmetic and one consistent rounding policy. I would study PINT AE rounding requirements and tax calculation test design.
- **Back-pressure and retries:** HTTP 429 plus `Retry-After` needs durable retry state, bounded backoff and observability. I would study queue/outbox patterns and at-least-once delivery with idempotent consumers.
- **Incident response:** restart counts alone do not prove OOM. I would correlate container exit reason, memory, logs, 5xx rates, queue depth and invoice state transitions before declaring a root cause.
- **Support communication:** explain what is known, what is not known, what the customer should do now and when the next update will arrive. Do not overpromise a fix date or tell customers to resend before reconciliation.

### Time log (real time)

| Date | Fromâ€“to | What I worked on |
|---|---|---|
| 14 Nov 2026 | Exact overall start/end time not captured | Inspected assignment materials and source; audited workbooks; started and verified the Docker Compose stack; replayed Oasis, Al Noor, Bluepeak/Sahara and Ghaf; queried PostgreSQL; inspected logs, health endpoints, Prometheus targets and container resources; saved runtime evidence. Exact total elapsed time is not claimed because it was not recorded. |

### AI usage disclosure

- **ChatGPT (OpenAI):** used to inspect the supplied assignment/repository, structure the investigation, review code paths, calculate workbook-derived evidence and draft this submission. The workbook audit script is included in `evidence/workbook_audit.py`; its output is `evidence/workbook-audit-output.txt`.
- **Python / openpyxl:** used locally for read-only inspection of the supplied `.xlsx` workbooks and deterministic reproduction of the PINT total formula found in source. This did not execute the application or contact the ASP.
- **Verification:** Source references and workbook calculations were checked. Docker Compose was used to start the local stack and replay four scenarios. PostgreSQL queries, API/ASP logs, health endpoints, Prometheus targets and container resource data were captured. Oasis original replay completed with eight accepted invoices in 123.7 seconds. A controlled repeat upload timed out at the client after 60 seconds, while the API continued and completed after 121.64 seconds with eight portal rejections. The results are consistent with the duplicate-number guard. Al Noor BR-CO-15 rejections, Bluepeak/Sahara HTTP 429 rate limiting, and Ghaf AE-BR-04 date validation failures were reproduced. Marina Bay was not independently reproduced. Evidence is saved under `evidence/runtime/` and `evidence/screenshots/`.- **Other AI tools:** none used in this work session.

---

## Final requirement audit

| Requirement from original instructions | Status | Evidence / note |
|---|---|---|
| Acknowledgement draft for all five items with exercise-clock time | PASS | All five incident sections include a draft response and time. |
| Priority P1â€“P4 and reason for all five | PASS | All five sections include priority and justification; Marina Bay is explicitly provisional. |
| Full investigation for at least three incidents | PASS | Al Noor, Bluepeak/Sahara and Ghaf have runtime reproductions supported by logs, database results and source references. |
| Investigation logs including dead ends | PARTIAL | Ordered investigation sequences and dead ends are documented; actual exercise-clock investigation timestamps were not recorded and are not invented. |
| Root cause backed by evidence and file:line | PASS | Three reproduced incidents have runtime evidence and source references. Oasis and Marina Bay limitations are explicitly documented. |
| Customer reply or complete escalation note; L1 ownership retained | PASS / PARTIAL | Draft replies and escalation templates are present. Runtime-specific affected IDs and response evidence remain unavailable. |
| Workaround and prevention ideas for investigated items | PASS | Included in all detailed incident sections. |
| Remaining incident next checks | PASS | Incident 2 identifies precise runtime checks still required; runtime root cause is not claimed. |
| Overall prioritisation, reflection and learning | PASS | Included. |
| Real-time time log | PARTIAL | Work session recorded honestly; exact end and elapsed duration not captured. Update before submission if possible. |
| AI usage disclosure | PASS | Tools, use and verification limits disclosed. |
| `evidence/` folder with supporting files linked from submission | PASS | Runtime logs, PostgreSQL outputs, health checks, Prometheus targets, container results and screenshots are included. |
| Push repository to own GitHub account | NOT DONE | Requires user-created repository and approval; current `origin` still points to assignment author's repository. |
| Submit Microsoft Form using application email | NOT DONE | User must complete after pushing a public repository. |

**Honest completion status:** Four incident scenarios have been replayed and runtime evidence captured. Marina Bay remains unconfirmed. The submission document and evidence package still require a final consistency and secret-safety check. The repository has not yet been pushed to the user's own public GitHub repository, and the Microsoft Form has not yet been submitted.









