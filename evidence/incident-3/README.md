# Incident 3 — Al Noor Fuel

Evidence source: `../workbook-audit-output.txt`, `../source-code-findings.md`.

The supplied workbook contains six invoices. Reproduction of the source calculation shows BR-CO-15 arithmetic mismatches for 0042 (-AED 0.01), 0044 (-AED 0.02), and 0046 (-AED 0.01). Source computes line VAT from rounded line net, but gross from unrounded quantity × unit price × 1.05. ASP mock compares rounded cents of gross to net plus VAT.

This is deterministic workbook/source arithmetic, not a live ASP response. Confirm stored payload and ASP response in a running environment.
