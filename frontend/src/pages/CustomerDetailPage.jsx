import { useEffect, useState } from "react";
import { navigate } from "../hooks/useRoute";
import CustomerLayout from "../layouts/CustomerLayout";
import { getErrorMessage } from "../services/api";
import { getCustomer } from "../services/customers";

const Detail = ({ label, value, children }) => value ? <div><dt className="text-sm text-slate-500">{label}</dt><dd className="mt-1 whitespace-pre-wrap font-medium text-slate-800">{children || value}</dd></div> : null;

export default function CustomerDetailPage({ customerId }) {
  const [customer, setCustomer] = useState(null);
  const [error, setError] = useState("");
  useEffect(() => { getCustomer(customerId).then(setCustomer).catch((requestError) => setError(getErrorMessage(requestError))); }, [customerId]);
  return (
    <CustomerLayout title="اطلاعات مشتری" showBack>
      <div className="mx-auto max-w-2xl">
        {error && <p className="rounded-xl bg-red-50 p-3 text-sm text-red-700">{error}</p>}
        {!error && !customer && <p className="py-12 text-center text-slate-600">در حال دریافت مشتری…</p>}
        {customer && <section className="rounded-2xl bg-white p-5 shadow-sm ring-1 ring-slate-200 sm:p-7">
          <div className="flex items-start justify-between gap-3"><div><h2 className="text-xl font-bold text-slate-900">{customer.name}</h2>{customer.company_name && <p className="mt-1 text-slate-500">{customer.company_name}</p>}</div><button className="min-h-11 rounded-xl border border-slate-300 px-4 font-semibold" onClick={() => navigate("/customers/" + customer.id + "/edit")} type="button">ویرایش</button></div>
          <div className="mt-5 grid grid-cols-2 gap-3"><button className="min-h-12 rounded-xl bg-teal-700 px-4 font-semibold text-white hover:bg-teal-800" onClick={() => navigate("/customers/" + customer.id + "/orders/new")} type="button">ثبت سفارش</button><button className="min-h-12 rounded-xl border border-teal-700 px-4 font-semibold text-teal-800 hover:bg-teal-50" onClick={() => navigate("/customers/" + customer.id + "/purchases/new")} type="button">ثبت خرید</button></div>
          <dl className="mt-7 grid gap-5 sm:grid-cols-2">
            <Detail label="شماره تماس" value={customer.phone_number}>{customer.phone_number && <a className="text-teal-700" dir="ltr" href={"tel:" + customer.phone_number}>{customer.phone_number}</a>}</Detail>
            <Detail label="نام شرکت" value={customer.company_name} />
            <Detail label="کد اقتصادی" value={customer.economic_code} />
            <Detail label="کد پستی" value={customer.postal_code} />
            <Detail label="نشانی" value={customer.address} />
            <Detail label="توضیحات" value={customer.description} />
          </dl>
        </section>}
      </div>
    </CustomerLayout>
  );
}
