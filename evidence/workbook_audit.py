"""Read-only audit of the supplied customer workbooks; does not modify source files."""
from collections import Counter, defaultdict
from pathlib import Path
import math
import openpyxl

ROOT = Path(__file__).resolve().parents[1]
SAMPLES = ROOT / "samples"

def money(x):
    # Go math.Round(x*100)/100 for the positive AED amounts in these samples.
    return math.floor(float(x) * 100 + 0.5) / 100

for name in [
    "oasis-builders-nov-2026.xlsx",
    "al-noor-fuel-nov-2026.xlsx",
    "sahara-medical-batch-1116.xlsx",
    "ghaf-cafe-nov-2026.xlsx",
]:
    path = SAMPLES / name
    workbook = openpyxl.load_workbook(path, data_only=True, read_only=False)
    ws = workbook["Invoices"]
    rows = list(ws.iter_rows(values_only=True))
    headers = list(rows[0])
    idx = {h: i for i, h in enumerate(headers)}
    data = rows[1:]
    grouped = defaultdict(list)
    for row in data:
        grouped[row[idx["Invoice number*"]]].append(row)
    print(f"\n{name}: data_rows={len(data)}, unique_invoices={len(grouped)}")
    print(f"  invoice_numbers={','.join(grouped)}")
    if name.startswith("oasis"):
        print(f"  lines_per_invoice={dict(Counter(map(len, grouped.values())))}")
        print(f"  unique_buyer_participants={len(set(r[idx['Buyer Peppol Id*']] for r in data))}")
        print("  modelled_directory_calls=600 (one per data row; code validates each row individually)")
        print("  modelled_lookup_time_at_200ms_each=120 seconds (600 x 0.2s; sequential code path)")
    elif name.startswith("al-noor"):
        print("  invoice,lines,net,vat,gross_code_formula,expected_net_plus_vat,difference")
        for number, lines in grouped.items():
            net = sum(float(r[idx["Invoice line net amount*"]]) for r in lines)
            vat = sum(money(float(r[idx["Invoice line net amount*"]]) * float(r[idx["Invoiced item VAT rate*"]]) / 100) for r in lines)
            gross = money(sum(float(r[idx["Itemquantity*"]]) * float(r[idx["Item net price*"]]) * (1 + float(r[idx["Invoiced item VAT rate*"]]) / 100) for r in lines))
            expected = money(money(net) + money(vat))
            print(f"  {number},{len(lines)},{money(net):.2f},{money(vat):.2f},{gross:.2f},{expected:.2f},{gross-expected:+.2f}")
        print("  expected_BR_CO_15_mismatches=3 (0042, 0044, 0046); this is a source-formula reproduction, not an ASP runtime test")
    elif name.startswith("sahara"):
        print(f"  unique_buyer_participants={len(set(r[idx['Buyer Peppol Id*']] for r in data))}")
        print("  ASP_limit_from_source=burst 8 then refill 2 documents/second per sender")
        print("  if 40 requests arrive in one burst, initial capacity is 8; 429 handling in API is not implemented")
    elif name.startswith("ghaf"):
        for col in ["Invoice issue date*", "Payment due date*"]:
            vals = [r[idx[col]] for r in data]
            print(f"  {col}: cell_types={dict(Counter(type(v).__name__ for v in vals))}; values={dict(Counter(vals))}")
        print("  4 invoices; both mandatory date columns are text in slash format")
