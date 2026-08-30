import { useEffect, useState } from "react";
import OrderLayout from "../layouts/OrderLayout";
import { navigate } from "../hooks/useRoute";
import { getErrorMessage } from "../services/api";
import { downloadInvoicePdf, getInvoice } from "../services/invoices";
import { formatPrice } from "../services/products";

const Info = ({ label, value }) => value ? <div><dt className="text-sm text-slate-500">{label}</dt><dd className="mt-1 whitespace-pre-wrap font-medium">{value}</dd></div> : null;

export default function InvoiceDetailPage({ invoiceId }) {
  const [invoice, setInvoice] = useState(null);
  const [error, setError] = useState("");
  const [isDownloading, setIsDownloading] = useState(false);
  useEffect(() => { getInvoice(invoiceId).then(setInvoice).catch((requestError) => setError(getErrorMessage(requestError))); }, [invoiceId]);
  const openPdf = async (print = false) => {
    setError(""); setIsDownloading(true);
    try {
      const blob = await downloadInvoicePdf(invoiceId);
      const url = URL.createObjectURL(blob);
      if (print) {
        window.open(url, "_blank", "noopener,noreferrer");
        window.setTimeout(() => URL.revokeObjectURL(url), 60000);
      } else {
        const link = document.createElement("a");
        link.href = url;
        link.download = "invoice-" + invoice.invoice_number + ".pdf";
        link.click();
        URL.revokeObjectURL(url);
      }
    } catch (requestError) { setError(getErrorMessage(requestError)); }
    finally { setIsDownloading(false); }
  };
  return <OrderLayout title="جزئیات فاکتور" backPath="/invoices"><div className="mx-auto max-w-5xl">
    {error && <p className="rounded-xl bg-red-50 p-3 text-sm text-red-700">{error}</p>}
    {!invoice && !error && <p className="py-12 text-center text-slate-600">در حال دریافت فاکتور…</p>}
    {invoice && <div className="space-y-4"><header className="rounded-2xl bg-white p-5 ring-1 ring-slate-200 sm:p-7"><div className="flex flex-wrap items-start justify-between gap-4"><div><p className="font-mono text-sm text-teal-700" dir="ltr">{invoice.invoice_number}</p><h2 className="mt-1 text-2xl font-bold">فاکتور فروش</h2><p className="mt-1 text-sm text-slate-600">نسخه {new Intl.NumberFormat("fa-IR").format(invoice.revision_number)}</p></div><div className="text-left text-sm text-slate-600"><p>{new Intl.DateTimeFormat("fa-IR", { dateStyle: "long", timeStyle: "short" }).format(new Date(invoice.issued_at))}</p><p className="mt-1">وضعیت: {invoice.status_display}</p></div></div>{invoice.status === "superseded" && <p className="mt-4 rounded-xl bg-amber-50 p-3 text-sm text-amber-800">این فاکتور با نسخه جدید جایگزین شده است.</p>}<div className="mt-4 grid gap-2 sm:grid-cols-2">{invoice.previous_invoice && <button className="min-h-11 rounded-xl border border-slate-300 font-semibold" onClick={() => navigate("/invoices/" + invoice.previous_invoice.id)} type="button">مشاهده نسخه قبلی</button>}{invoice.replacement_invoice && <button className="min-h-11 rounded-xl border border-teal-700 font-semibold text-teal-800" onClick={() => navigate("/invoices/" + invoice.replacement_invoice.id)} type="button">مشاهده نسخه جدید</button>}</div><div className="mt-5 grid grid-cols-2 gap-3"><button className="min-h-12 rounded-xl bg-teal-700 px-4 font-semibold text-white disabled:opacity-60" disabled={isDownloading} onClick={() => openPdf(false)} type="button">{isDownloading ? "در حال آماده‌سازی…" : "دانلود PDF"}</button><button className="min-h-12 rounded-xl border border-teal-700 px-4 font-semibold text-teal-800 disabled:opacity-60" disabled={isDownloading} onClick={() => openPdf(true)} type="button">چاپ فاکتور</button></div></header>
      <div className="grid gap-4 md:grid-cols-2"><section className="rounded-2xl bg-white p-5 ring-1 ring-slate-200"><h3 className="mb-4 font-bold text-teal-800">فروشنده</h3><dl className="grid gap-4 sm:grid-cols-2"><Info label="نام" value={invoice.seller_name} /><Info label="شماره تماس" value={invoice.seller_phone_number} /><Info label="کد اقتصادی" value={invoice.seller_economic_code} /><Info label="شناسه ملی" value={invoice.seller_national_id} /><Info label="شماره ثبت" value={invoice.seller_registration_number} /><Info label="کد پستی" value={invoice.seller_postal_code} /><Info label="نشانی" value={invoice.seller_address} /></dl></section>
      <section className="rounded-2xl bg-white p-5 ring-1 ring-slate-200"><h3 className="mb-4 font-bold text-teal-800">خریدار</h3><dl className="grid gap-4 sm:grid-cols-2"><Info label="نام" value={invoice.buyer_name} /><Info label="نام شرکت" value={invoice.buyer_company_name} /><Info label="شماره تماس" value={invoice.buyer_phone_number} /><Info label="کد اقتصادی" value={invoice.buyer_economic_code} /><Info label="کد پستی" value={invoice.buyer_postal_code} /><Info label="نشانی" value={invoice.buyer_address} /></dl></section></div>
      <section className="space-y-3">{invoice.items.map((item) => <article className="rounded-2xl bg-white p-4 ring-1 ring-slate-200" key={item.id}><div className="flex justify-between gap-3"><div><h3 className="font-bold">{item.product_name}</h3>{item.brand && <p className="text-sm text-slate-500">{item.brand}</p>}</div><span className="font-semibold text-teal-800">{formatPrice(item.line_total)}</span></div><div className="mt-3 grid grid-cols-3 gap-2 text-sm text-slate-600"><span>مقدار: {new Intl.NumberFormat("fa-IR").format(Number(item.quantity))}</span><span>واحد: {item.unit}</span><span>قیمت: {formatPrice(item.unit_price)}</span></div></article>)}</section>
      <section className="mr-auto w-full rounded-2xl bg-white p-5 ring-1 ring-slate-200 sm:max-w-md"><dl className="space-y-3"><div className="flex justify-between"><dt>جمع اقلام</dt><dd>{formatPrice(invoice.subtotal)}</dd></div><div className="flex justify-between"><dt>تخفیف</dt><dd>{formatPrice(invoice.discount_amount)}</dd></div><div className="flex justify-between"><dt>مالیات</dt><dd>{formatPrice(invoice.tax_amount)}</dd></div><div className="flex justify-between"><dt>عوارض</dt><dd>{formatPrice(invoice.duties_amount)}</dd></div><div className="flex justify-between border-t border-slate-200 pt-3 text-lg font-bold text-teal-800"><dt>مبلغ نهایی</dt><dd>{formatPrice(invoice.final_amount)}</dd></div></dl></section>
      {invoice.notes && <section className="rounded-2xl bg-white p-5 ring-1 ring-slate-200"><h3 className="text-sm text-slate-500">یادداشت</h3><p className="mt-2 whitespace-pre-wrap">{invoice.notes}</p></section>}
      {invoice.status === "issued" && invoice.items.some((item) => Number(item.remaining_returnable_quantity) > 0) && <button className="min-h-12 w-full rounded-xl border border-teal-700 font-semibold text-teal-800" onClick={() => navigate("/invoices/" + invoice.id + "/returns/new")} type="button">ثبت مرجوعی</button>}
    </div>}
  </div></OrderLayout>;
}
