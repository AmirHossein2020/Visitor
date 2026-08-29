import { useState } from "react";
import FormField from "./FormField";

const emptyProfile = {
  name: "", phone_number: "", address: "", economic_code: "",
  national_id: "", registration_number: "", postal_code: "", description: "",
};

export default function SellerProfileForm({ initialValue = emptyProfile, onSubmit, submitLabel }) {
  const [form, setForm] = useState({ ...emptyProfile, ...initialValue });
  const [error, setError] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const update = (event) => setForm({ ...form, [event.target.name]: event.target.value });
  const submit = async (event) => {
    event.preventDefault(); setError("");
    if (!form.name.trim()) return setError("نام فروشنده یا شرکت الزامی است.");
    if (form.phone_number && !/^[0-9+()\-\s]{7,25}$/.test(form.phone_number)) return setError("شماره تماس واردشده معتبر نیست.");
    setIsSubmitting(true);
    try { await onSubmit(form); } catch (message) { setError(typeof message === "string" ? message : "ثبت اطلاعات انجام نشد."); }
    finally { setIsSubmitting(false); }
  };
  return <form className="space-y-4 rounded-2xl bg-white p-5 shadow-sm ring-1 ring-slate-200 sm:p-7" onSubmit={submit}>
    <FormField id="seller_name" name="name" label="نام فروشنده / شرکت" maxLength="200" required disabled={isSubmitting} value={form.name} onChange={update} />
    <FormField id="seller_phone" name="phone_number" label="شماره تماس (اختیاری)" type="tel" maxLength="25" disabled={isSubmitting} value={form.phone_number} onChange={update} />
    <FormField id="economic_code" name="economic_code" label="کد اقتصادی (اختیاری)" maxLength="30" disabled={isSubmitting} value={form.economic_code} onChange={update} />
    <FormField id="national_id" name="national_id" label="شناسه ملی (اختیاری)" maxLength="30" disabled={isSubmitting} value={form.national_id} onChange={update} />
    <FormField id="registration_number" name="registration_number" label="شماره ثبت (اختیاری)" maxLength="30" disabled={isSubmitting} value={form.registration_number} onChange={update} />
    <FormField id="seller_postal_code" name="postal_code" label="کد پستی (اختیاری)" maxLength="20" disabled={isSubmitting} value={form.postal_code} onChange={update} />
    <label className="block" htmlFor="seller_address"><span className="mb-1.5 block text-sm font-medium text-slate-700">نشانی (اختیاری)</span><textarea id="seller_address" name="address" maxLength="500" className="min-h-24 w-full rounded-xl border border-slate-300 p-3" disabled={isSubmitting} value={form.address} onChange={update} /></label>
    <label className="block" htmlFor="seller_description"><span className="mb-1.5 block text-sm font-medium text-slate-700">توضیحات (اختیاری)</span><textarea id="seller_description" name="description" className="min-h-24 w-full rounded-xl border border-slate-300 p-3" disabled={isSubmitting} value={form.description} onChange={update} /></label>
    {error && <p className="rounded-xl bg-red-50 p-3 text-sm text-red-700">{error}</p>}
    <button className="min-h-12 w-full rounded-xl bg-teal-700 px-4 font-semibold text-white disabled:opacity-60" disabled={isSubmitting} type="submit">{isSubmitting ? "در حال ذخیره…" : submitLabel}</button>
  </form>;
}
