import { useState } from "react";
import FormField from "./FormField";
import { normalizePhone } from "../services/normalization";

const emptyCustomer = {
  name: "", phone_number: "", company_name: "", address: "",
  economic_code: "", postal_code: "", description: "",
};

export default function CustomerForm({ initialValue = emptyCustomer, onSubmit, submitLabel }) {
  const [form, setForm] = useState({ ...emptyCustomer, ...initialValue });
  const [error, setError] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const update = (event) => setForm({ ...form, [event.target.name]: event.target.value });
  const submit = async (event) => {
    event.preventDefault();
    setError("");
    if (!form.name.trim()) return setError("نام مشتری الزامی است.");
    const normalized = { ...form, phone_number: normalizePhone(form.phone_number) };
    if (normalized.phone_number && !/^[0-9+()\-\s]{7,25}$/.test(normalized.phone_number)) return setError("شماره تماس واردشده معتبر نیست.");
    setIsSubmitting(true);
    try {
      await onSubmit(normalized);
    } catch (message) {
      setError(typeof message === "string" ? message : "ثبت اطلاعات انجام نشد.");
    } finally {
      setIsSubmitting(false);
    }
  };
  return (
    <form className="space-y-4 rounded-2xl bg-white p-5 shadow-sm ring-1 ring-slate-200 sm:p-7" onSubmit={submit}>
      <FormField id="customer_name" name="name" label="نام مشتری" maxLength="200" required disabled={isSubmitting} value={form.name} onChange={update} />
      <FormField id="phone_number" name="phone_number" label="شماره تماس (اختیاری)" type="tel" inputMode="tel" maxLength="25" disabled={isSubmitting} value={form.phone_number} onChange={update} />
      <FormField id="company_name" name="company_name" label="نام شرکت (اختیاری)" maxLength="200" disabled={isSubmitting} value={form.company_name} onChange={update} />
      <FormField id="economic_code" name="economic_code" label="کد اقتصادی (اختیاری)" maxLength="30" disabled={isSubmitting} value={form.economic_code} onChange={update} />
      <FormField id="postal_code" name="postal_code" label="کد پستی (اختیاری)" maxLength="20" disabled={isSubmitting} value={form.postal_code} onChange={update} />
      <label className="block" htmlFor="address"><span className="mb-1.5 block text-sm font-medium text-slate-700">نشانی (اختیاری)</span><textarea id="address" name="address" maxLength="500" className="min-h-24 w-full resize-y rounded-xl border border-slate-300 px-3.5 py-3 outline-none focus:border-teal-600 focus:ring-2 focus:ring-teal-100" disabled={isSubmitting} value={form.address} onChange={update} /></label>
      <label className="block" htmlFor="customer_description"><span className="mb-1.5 block text-sm font-medium text-slate-700">توضیحات (اختیاری)</span><textarea id="customer_description" name="description" className="min-h-24 w-full resize-y rounded-xl border border-slate-300 px-3.5 py-3 outline-none focus:border-teal-600 focus:ring-2 focus:ring-teal-100" disabled={isSubmitting} value={form.description} onChange={update} /></label>
      {error && <p className="rounded-xl bg-red-50 px-3 py-2 text-sm text-red-700" role="alert">{error}</p>}
      <button className="min-h-12 w-full rounded-xl bg-teal-700 px-4 font-semibold text-white hover:bg-teal-800 disabled:opacity-60" disabled={isSubmitting} type="submit">{isSubmitting ? "در حال ذخیره…" : submitLabel}</button>
    </form>
  );
}
