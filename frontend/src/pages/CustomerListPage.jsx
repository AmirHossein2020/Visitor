import { useCallback, useEffect, useState } from "react";
import { navigate } from "../hooks/useRoute";
import CustomerLayout from "../layouts/CustomerLayout";
import { getErrorMessage } from "../services/api";
import { deactivateCustomer, listCustomers } from "../services/customers";

export default function CustomerListPage() {
  const [customers, setCustomers] = useState([]);
  const [search, setSearch] = useState("");
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState("");
  const load = useCallback(async (term = "") => {
    setIsLoading(true); setError("");
    try { setCustomers(await listCustomers(term)); }
    catch (requestError) { setError(getErrorMessage(requestError)); }
    finally { setIsLoading(false); }
  }, []);
  useEffect(() => { load(); }, [load]);
  const remove = async (customer) => {
    if (!window.confirm("این مشتری غیرفعال شود؟")) return;
    try {
      await deactivateCustomer(customer.id);
      setCustomers((items) => items.filter((item) => item.id !== customer.id));
    } catch (requestError) { setError(getErrorMessage(requestError)); }
  };
  return (
    <CustomerLayout title="مشتری‌ها">
      <div className="mb-5 flex flex-col gap-3 sm:flex-row">
        <form className="flex flex-1 gap-2" onSubmit={(event) => { event.preventDefault(); load(search.trim()); }}>
          <input aria-label="جستجوی مشتری" className="min-h-12 min-w-0 flex-1 rounded-xl border border-slate-300 bg-white px-4 outline-none focus:border-teal-600 focus:ring-2 focus:ring-teal-100" placeholder="جستجو در نام، شرکت یا تلفن" value={search} onChange={(event) => setSearch(event.target.value)} />
          <button className="min-h-12 rounded-xl border border-slate-300 bg-white px-4 font-semibold text-slate-700" type="submit">جستجو</button>
        </form>
        <button className="min-h-12 rounded-xl bg-teal-700 px-5 font-semibold text-white" onClick={() => navigate("/customers/new")} type="button">افزودن مشتری</button>
      </div>
      {error && <p className="mb-4 rounded-xl bg-red-50 px-3 py-2 text-sm text-red-700" role="alert">{error}</p>}
      {isLoading ? <p className="py-12 text-center text-slate-600">در حال دریافت مشتری‌ها…</p> : customers.length === 0 ? <div className="rounded-2xl bg-white py-12 text-center text-slate-600 ring-1 ring-slate-200">مشتری‌ای پیدا نشد.</div> : (
        <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
          {customers.map((customer) => (
            <article className="rounded-2xl bg-white p-5 shadow-sm ring-1 ring-slate-200" key={customer.id}>
              <button className="min-h-11 w-full text-right" onClick={() => navigate("/customers/" + customer.id)} type="button">
                <h2 className="text-lg font-bold text-slate-900">{customer.name}</h2>
                {customer.company_name && <p className="mt-1 text-sm text-slate-500">{customer.company_name}</p>}
              </button>
              {customer.phone_number && <a className="mt-3 inline-flex min-h-11 items-center font-semibold text-teal-700" dir="ltr" href={"tel:" + customer.phone_number}>{customer.phone_number}</a>}
              <div className="mt-4 grid grid-cols-3 gap-2">
                <button className="min-h-11 rounded-xl border border-slate-300 text-sm font-semibold" onClick={() => navigate("/customers/" + customer.id)} type="button">مشاهده</button>
                <button className="min-h-11 rounded-xl border border-slate-300 text-sm font-semibold" onClick={() => navigate("/customers/" + customer.id + "/edit")} type="button">ویرایش</button>
                <button className="min-h-11 rounded-xl border border-red-200 text-sm font-semibold text-red-700" onClick={() => remove(customer)} type="button">غیرفعال</button>
              </div>
            </article>
          ))}
        </div>
      )}
    </CustomerLayout>
  );
}
