# Evidence index

This folder contains evidence derived from the supplied repository and sample workbooks.

| File | Purpose | Evidence type / limitation |
|---|---|---|
| `workbook_audit.py` | Read-only workbook inspection and source-formula reproduction | Locally executed against supplied `.xlsx` files; does not start the application |
| `workbook-audit-output.txt` | Actual output from the workbook audit | Locally executed output |
| `source-code-findings.md` | File/line references supporting all five incident analyses | Static source inspection, not runtime evidence |
| `environment/runtime-checks.txt` | Docker/Go/psql availability, toolchain download and `make up` attempt | Actual environment check output |
| `environment/diagnostics.sql` | Queries to run once PostgreSQL is available | Prepared only; **NOT EXECUTED** |
| `incident-1/`–`incident-5/` | Incident-specific notes and next checks | Static/data analysis unless explicitly marked otherwise |

No screenshots, live application logs, Grafana panels, Prometheus query results, PostgreSQL query results, or ASP API responses are included because the lab stack could not be started in this environment. Do not represent these as collected evidence.
