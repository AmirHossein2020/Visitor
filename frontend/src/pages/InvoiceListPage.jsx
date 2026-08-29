import { useEffect, useState } from "react";
import { navigate } from "../hooks/useRoute";
import OrderLayout from "../layouts/OrderLayout";
import { getErrorMessage } from "../services/api";
import { listInvoices } from "../services/invoices";
import { formatPrice } from "../services/products";

export default function InvoiceListPage() {
  const [invoices, setInvoices] = useState([]);
  const [error, setError] = useState("");
  const [isLoading, setIsLoading] = useState(true);
  useEffect(() => { listInvoices().then(setInvoices).catch((requestError) => setError(getErrorMessage(requestError))).finally(() => setIsLoading(false)); }, []);
  return <OrderLayout title="فاکتورها" backPath="/">
    {error && <p className="rounded-xl bg-red-50 p-3 text-sm text-red-700">{error}</p>}
    {isLoading ? <p className="py-12 text-center text-slate-600">در حال دریافت فاکتورها…</p> : invoices.length === 0 ? <div className="rounded-2xl bg-white py-12 text-center text-slate-600 ring-1 ring-slate-200">فاکتوری صادر نشده است.</div> : <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">{invoices.map((invoice) => <button className="min-h-36 rounded-2xl bg-white p-5 text-right ring-1 ring-slate-200 hover:ring-teal-300" key={invoice.id} onClick={() => navigate("/invoices/" + invoice.id)} type="button"><span className="block font-mono text-sm text-teal-700" dir="ltr">{invoice.invoice_number}</span><span className="mt-2 block text-lg font-bold">{invoice.buyer_name}</span><span className="mt-1 block text-sm text-slate-500">فروشنده: {invoice.seller_name}</span><span className="mt-3 block text-sm text-slate-500">{new Intl.DateTimeFormat("fa-IR").format(new Date(invoice.issued_at))} · {invoice.status_display}</span><span className="mt-2 block font-semibold text-teal-800">{formatPrice(invoice.final_amount)} تومان</span></button>)}</div>}
  </OrderLayout>;
}
