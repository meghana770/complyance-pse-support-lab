# Incident 5 — Ghaf Tree Café

Evidence source: `../workbook-audit-output.txt`, `../source-code-findings.md`, `../environment/runtime-checks.txt`.

Workbook has four invoice numbers/eight data rows. All eight issue-date and due-date cells are text strings in slash-separated format. Parser accepts ISO date strings or numeric Excel serials; validator checks both columns and returns AE-BR-04. Template guide documents this behaviour.

This is expected behaviour under the supplied documentation. A corrected workbook was not uploaded because the application could not be started.
