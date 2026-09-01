export function formatMoney(value) {
  const raw = String(value ?? "0").trim().replaceAll(",", "");
  const match = raw.match(/^(-?)(\d+)(?:\.(\d+))?$/);
  if (!match) return "۰ ریال";

  const [, sign, integer, decimal = ""] = match;
  const groupedInteger = new Intl.NumberFormat("fa-IR", { maximumFractionDigits: 0 })
    .format(BigInt(`${sign}${integer}`));
  const meaningfulDecimal = decimal.replace(/0+$/, "");
  const localizedDecimal = meaningfulDecimal.replace(/[0-9]/g, (digit) => "۰۱۲۳۴۵۶۷۸۹"[Number(digit)]);
  return `${groupedInteger}${localizedDecimal ? `٫${localizedDecimal}` : ""} ریال`;
}

export function formatDateTime(value) {
  return formatJalaliDateTime(value);
}
import { formatJalaliDateTime } from "./jalali";
