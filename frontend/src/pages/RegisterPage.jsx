import { useState } from "react";
import AuthLayout from "../components/AuthLayout";
import FormField from "../components/FormField";
import { navigate } from "../hooks/useRoute";
import { useAuth } from "../services/AuthContext";
import { getErrorMessage } from "../services/api";

const initialForm = { full_name: "", email: "", phone_number: "", password: "", password_confirm: "" };

export default function RegisterPage() {
  const { register, login } = useAuth();
  const [form, setForm] = useState(initialForm);
  const [error, setError] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);

  const update = (event) => setForm({ ...form, [event.target.name]: event.target.value });
  const submit = async (event) => {
    event.preventDefault();
    setError("");
    if (form.password !== form.password_confirm) {
      setError("رمزهای عبور یکسان نیستند.");
      return;
    }
    setIsSubmitting(true);
    try {
      await register(form);
      await login({ email: form.email, password: form.password });
      navigate("/pricing", { replace: true });
    } catch (requestError) {
      setError(getErrorMessage(requestError));
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <AuthLayout
      title="ثبت‌نام"
      subtitle="اطلاعات پایه حساب ویزیتوری خود را وارد کنید."
      footer={<><span>قبلاً ثبت‌نام کرده‌اید؟ </span><button className="font-semibold text-teal-700" onClick={() => navigate("/login")} type="button">ورود</button></>}
    >
      <form className="space-y-4" onSubmit={submit}>
        <FormField id="full_name" name="full_name" label="نام و نام خانوادگی" autoComplete="name" required disabled={isSubmitting} value={form.full_name} onChange={update} />
        <FormField id="register_email" name="email" label="ایمیل" type="email" autoComplete="email" required disabled={isSubmitting} value={form.email} onChange={update} />
        <FormField id="phone_number" name="phone_number" label="شماره موبایل (اختیاری)" type="tel" inputMode="tel" autoComplete="tel" disabled={isSubmitting} value={form.phone_number} onChange={update} />
        <FormField id="register_password" name="password" label="رمز عبور" type="password" autoComplete="new-password" minLength="8" required disabled={isSubmitting} value={form.password} onChange={update} />
        <FormField id="password_confirm" name="password_confirm" label="تکرار رمز عبور" type="password" autoComplete="new-password" minLength="8" required disabled={isSubmitting} value={form.password_confirm} onChange={update} />
        {error && <p className="rounded-xl bg-red-50 px-3 py-2 text-sm leading-6 text-red-700" role="alert">{error}</p>}
        <button className="min-h-12 w-full rounded-xl bg-teal-700 px-4 font-semibold text-white transition hover:bg-teal-800 disabled:cursor-not-allowed disabled:opacity-60" disabled={isSubmitting} type="submit">
          {isSubmitting ? "در حال ثبت‌نام…" : "ثبت‌نام"}
        </button>
      </form>
    </AuthLayout>
  );
}
