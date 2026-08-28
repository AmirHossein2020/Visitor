import { useEffect, useState } from "react";
import CustomerForm from "../components/CustomerForm";
import { navigate } from "../hooks/useRoute";
import CustomerLayout from "../layouts/CustomerLayout";
import { getErrorMessage } from "../services/api";
import { getCustomer, updateCustomer } from "../services/customers";

export default function CustomerEditPage({ customerId }) {
  const [customer, setCustomer] = useState(null);
  const [error, setError] = useState("");
  useEffect(() => { getCustomer(customerId).then(setCustomer).catch((requestError) => setError(getErrorMessage(requestError))); }, [customerId]);
  const submit = async (form) => {
    try { await updateCustomer(customerId, form); navigate("/customers/" + customerId, { replace: true }); }
    catch (requestError) { throw getErrorMessage(requestError); }
  };
  return <CustomerLayout title="ویرایش مشتری" showBack><div className="mx-auto max-w-xl">{error && <p className="rounded-xl bg-red-50 p-3 text-sm text-red-700">{error}</p>}{!error && !customer && <p className="py-12 text-center text-slate-600">در حال دریافت مشتری…</p>}{customer && <CustomerForm initialValue={customer} onSubmit={submit} submitLabel="ذخیره تغییرات" />}</div></CustomerLayout>;
}
