import type { ReconciliationResult, ReviewPacket } from "./types";

function row(values: (string | number | null | undefined)[]): string {
  return values
    .map((v) => {
      if (v === null || v === undefined) return "";
      const s = String(v);
      return /[",\n]/.test(s) ? `"${s.replace(/"/g, '""')}"` : s;
    })
    .join(",");
}

function matchSummaryRows(result: ReconciliationResult): string {
  const buckets = new Map<string, { purchases: number; gsts: number }>();
  const bump = (key: string) => {
    const b = buckets.get(key) ?? { purchases: 0, gsts: 0 };
    buckets.set(key, b);
    return b;
  };
  result.auto_matches.forEach(() => bump("auto_match"));
  result.review_packets.forEach((p) => {
    const b = bump(p.action);
    b.purchases += p.purchases.length;
    b.gsts += p.gsts.length;
  });
  const header = "match_status,inward_supply_count,purchase_count";
  const lines = [header];
  buckets.forEach((b, key) => lines.push(row([key, b.gsts, b.purchases])));
  return lines.join("\n");
}

function supplierRows(result: ReconciliationResult): string {
  const buckets = new Map<string, { name: string; gstin: string; purchases: number; gsts: number }>();
  const key = (gstin?: string | null, name?: string | null) => `${gstin ?? ""}|${name ?? ""}`;
  const visit = (packet: ReviewPacket) => {
    packet.purchases.forEach((r) => {
      const k = key(r.tax_identity, r.vendor_name);
      const b = buckets.get(k) ?? { name: r.vendor_name ?? "", gstin: r.tax_identity ?? "", purchases: 0, gsts: 0 };
      b.purchases += 1;
      buckets.set(k, b);
    });
    packet.gsts.forEach((r) => {
      const k = key(r.tax_identity, r.vendor_name);
      const b = buckets.get(k) ?? { name: r.vendor_name ?? "", gstin: r.tax_identity ?? "", purchases: 0, gsts: 0 };
      b.gsts += 1;
      buckets.set(k, b);
    });
  };
  result.review_packets.forEach(visit);
  const lines = ["supplier_name,supplier_gstin,inward_supply_count,purchase_count"];
  buckets.forEach((b) => lines.push(row([b.name, b.gstin, b.gsts, b.purchases])));
  return lines.join("\n");
}

function invoiceRows(result: ReconciliationResult): string {
  const header = [
    "match_status", "supplier_name", "supplier_gstin",
    "inward_supply_bill_no", "inward_supply_bill_date", "inward_supply_taxable_value",
    "purchase_bill_no", "purchase_bill_date", "purchase_taxable_value",
  ];
  const lines = [row(header)];
  result.review_packets.forEach((p) => {
    const n = Math.max(p.purchases.length, p.gsts.length, 1);
    for (let i = 0; i < n; i++) {
      const g = p.gsts[i];
      const pr = p.purchases[i];
      const name = pr?.vendor_name ?? g?.vendor_name ?? "";
      const gstin = pr?.tax_identity ?? g?.tax_identity ?? "";
      lines.push(
        row([
          p.action,
          name,
          gstin,
          g?.reference, g?.record_date, g?.taxable_value ?? g?.amount,
          pr?.reference, pr?.record_date, pr?.taxable_value ?? pr?.amount,
        ])
      );
    }
  });
  return lines.join("\n");
}

export type ReportKind = "match_summary" | "supplier" | "invoice";

export function buildReportCsv(result: ReconciliationResult, report: ReportKind): string {
  if (report === "match_summary") return matchSummaryRows(result);
  if (report === "supplier") return supplierRows(result);
  return invoiceRows(result);
}
