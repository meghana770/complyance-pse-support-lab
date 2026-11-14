-- Prepared for use if PostgreSQL becomes available. NOT EXECUTED in this environment.
-- 1) Import and invoice status overview for affected sellers.
SELECT s.name, i.id AS import_id, i.filename, i.status AS import_status,
       i.row_count, i.invoice_count, i.duration_ms, i.created_at, i.completed_at
FROM imports i JOIN sellers s ON s.id = i.seller_id
WHERE s.name IN ('Oasis Builders Supply LLC','Marina Bay Hospitality LLC',
                 'Al Noor Fuel & Lubricants LLC','Sahara Medical Supplies FZE',
                 'Ghaf Tree Café LLC')
ORDER BY i.created_at DESC;

-- 2) Invoice-level statuses, ASP references and stored errors.
SELECT s.name, v.invoice_number, v.status, v.rejected_by, v.asp_message_id,
       v.errors, v.asp_response, v.updated_at
FROM invoices v JOIN sellers s ON s.id = v.seller_id
WHERE (s.name = 'Oasis Builders Supply LLC' AND v.invoice_number LIKE 'OBS-2611-%')
   OR (s.name = 'Al Noor Fuel & Lubricants LLC' AND v.invoice_number LIKE 'ANF-2611-%')
   OR (s.name = 'Sahara Medical Supplies FZE' AND v.invoice_number LIKE 'SMS-1116-%')
   OR (s.name = 'Ghaf Tree Café LLC' AND v.invoice_number LIKE 'GTC-%')
ORDER BY s.name, v.invoice_number, v.created_at;

-- 3) Duplicate invoice numbers across imports (detects concurrent/repeated uploads).
SELECT seller_id, invoice_number, count(*) AS records,
       array_agg(status ORDER BY created_at) AS statuses,
       array_agg(import_id::text ORDER BY created_at) AS imports
FROM invoices
GROUP BY seller_id, invoice_number
HAVING count(*) > 1
ORDER BY seller_id, invoice_number;

-- 4) Status history for stuck invoices.
SELECT s.name, v.invoice_number, e.status, e.detail, e.created_at
FROM invoice_events e JOIN invoices v ON v.id = e.invoice_id
JOIN sellers s ON s.id = v.seller_id
WHERE v.status IN ('Validated','Submitted','Failed')
ORDER BY e.created_at DESC;
