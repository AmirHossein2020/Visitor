import { useState } from "react";
import AuthLayout from "../components/AuthLayout";
import FormField from "../components/FormField";
import { navigate } from "../hooks/useRoute";
import { useAuth } from "../services/AuthContext";
import { getErrorMessage } from "../services/api";
import { getMySubscription } from "../services/subscriptions";

export default function LoginPage() {
  const { login } = useAuth();
  const [form, setForm] = useState({ email: "", password: "" });
  const [error, setError] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const registrationComplete = new URLSearchParams(window.location.search).has("registered");

  const update = (event) => setForm({ ...form, [event.target.name]: event.target.value });
  const submit = async (event) => {
    event.preventDefault();
    setError("");
    setIsSubmitting(true);
    try {
      await login(form);
      const subscription = await getMySubscription();
      navigate(subscription.is_active ? "/app" : "/account/subscription", { replace: true });
    } catch (requestError) {
      setError(getErrorMessage(requestError));
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <AuthLayout
      title="ورود"
      subtitle="برای ادامه وارد حساب ویزیتوری خود شوید."
      footer={<><span>حساب ندارید؟ </span><button className="font-semibold text-teal-700" onClick={() => navigate("/register")} type="button">ثبت‌نام</button></>}
    >
      <form className="space-y-4" onSubmit={submit}>
        {registrationComplete && <p className="rounded-xl bg-emerald-50 px-3 py-2 text-sm leading-6 text-emerald-700" role="status">ثبت‌نام با موفقیت انجام شد. اکنون وارد شوید.</p>}
        <FormField id="email" name="email" label="ایمیل" type="email" autoComplete="email" required disabled={isSubmitting} value={form.email} onChange={update} />
        <FormField id="password" name="password" label="رمز عبور" type="password" autoComplete="current-password" required disabled={isSubmitting} value={form.password} onChange={update} />
        {error && <p className="rounded-xl bg-red-50 px-3 py-2 text-sm leading-6 text-red-700" role="alert">{error}</p>}
        <button className="min-h-12 w-full rounded-xl bg-teal-700 px-4 font-semibold text-white transition hover:bg-teal-800 disabled:cursor-not-allowed disabled:opacity-60" disabled={isSubmitting} type="submit">
          {isSubmitting ? "در حال ورود…" : "ورود"}
        </button>
      </form>
    </AuthLayout>
  );
}
