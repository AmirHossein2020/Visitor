import { useState } from "react";
import FormField from "./FormField";
import { units } from "../services/products";

const emptyProduct = {
  name: "",
  brand: "",
  default_price: "",
  unit: "",
  description: "",
};

export default function ProductForm({ initialValue = emptyProduct, onSubmit, submitLabel }) {
  const [form, setForm] = useState({ ...emptyProduct, ...initialValue });
  const [error, setError] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const update = (event) => setForm({ ...form, [event.target.name]: event.target.value });

  const submit = async (event) => {
    event.preventDefault();
    setError("");
    if (!form.name.trim()) return setError("نام محصول الزامی است.");
    if (form.default_price === "" || Number.isNaN(Number(form.default_price))) return setError("قیمت باید یک عدد معتبر باشد.");
    if (Number(form.default_price) < 0) return setError("قیمت نمی‌تواند منفی باشد.");
    if (!form.unit) return setError("واحد محصول الزامی است.");
    setIsSubmitting(true);
    try {
      await onSubmit(form);
    } catch (message) {
      setError(typeof message === "string" ? message : "ثبت اطلاعات انجام نشد.");
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <form className="space-y-4 rounded-2xl bg-white p-5 shadow-sm ring-1 ring-slate-200 sm:p-7" onSubmit={submit}>
      <FormField id="name" name="name" label="نام محصول" required disabled={isSubmitting} value={form.name} onChange={update} />
      <FormField id="brand" name="brand" label="برند (اختیاری)" disabled={isSubmitting} value={form.brand} onChange={update} />
      <FormField id="default_price" name="default_price" label="قیمت پیش‌فرض (تومان)" type="number" inputMode="decimal" min="0" step="0.01" required disabled={isSubmitting} value={form.default_price} onChange={update} />
      <label className="block" htmlFor="unit">
        <span className="mb-1.5 block text-sm font-medium text-slate-700">واحد</span>
        <select id="unit" name="unit" className="min-h-12 w-full rounded-xl border border-slate-300 bg-white px-3.5 text-base outline-none focus:border-teal-600 focus:ring-2 focus:ring-teal-100" required disabled={isSubmitting} value={form.unit} onChange={update}>
          <option value="">انتخاب واحد</option>
          {units.map((unit) => <option key={unit.value} value={unit.value}>{unit.label}</option>)}
        </select>
      </label>
      <label className="block" htmlFor="description">
        <span className="mb-1.5 block text-sm font-medium text-slate-700">توضیحات (اختیاری)</span>
        <textarea id="description" name="description" className="min-h-28 w-full resize-y rounded-xl border border-slate-300 bg-white px-3.5 py-3 text-base outline-none focus:border-teal-600 focus:ring-2 focus:ring-teal-100" disabled={isSubmitting} value={form.description} onChange={update} />
      </label>
      {error && <p className="rounded-xl bg-red-50 px-3 py-2 text-sm leading-6 text-red-700" role="alert">{error}</p>}
      <button className="min-h-12 w-full rounded-xl bg-teal-700 px-4 font-semibold text-white hover:bg-teal-800 disabled:opacity-60" disabled={isSubmitting} type="submit">{isSubmitting ? "در حال ذخیره…" : submitLabel}</button>
    </form>
  );
}
