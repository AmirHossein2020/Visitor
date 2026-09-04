import { useEffect, useState } from "react";
import { navigate } from "../hooks/useRoute";
import { getErrorMessage } from "../services/api";
import { activateFreeTrial, getMySubscription } from "../services/subscriptions";

export default function SubscriptionRequiredPage() {
  const [account, setAccount] = useState(null);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  useEffect(() => { getMySubscription().then(setAccount).catch((requestError) => setError(getErrorMessage(requestError))); }, []);
  const activate = async () => {
    setBusy(true); setError("");
    try { await activateFreeTrial(); window.location.assign("/app"); }
    catch (requestError) { setError(getErrorMessage(requestError)); setBusy(false); }
  };
  return <main className="grid min-h-dvh place-items-center bg-slate-50 p-4"><section className="w-full max-w-xl rounded-3xl bg-white p-7 text-center shadow-xl ring-1 ring-slate-200 sm:p-10"><span className="mx-auto grid size-14 place-items-center rounded-2xl bg-emerald-100 text-2xl">◇</span>{account?.trial_eligible ? <><h1 className="mt-5 text-2xl font-black">آزمایش رایگان یک‌روزه</h1><p className="mt-3 leading-8 text-slate-600">دسترسی کامل به پنل کسب‌وکار برای دقیقاً ۲۴ ساعت، بدون پرداخت و فقط یک‌بار.</p><button disabled={busy} className="mt-7 min-h-12 w-full rounded-xl bg-emerald-800 font-bold text-white disabled:opacity-60" onClick={activate}>{busy ? "در حال فعال‌سازی…" : "شروع آزمایش رایگان"}</button></> : <><h1 className="mt-5 text-2xl font-black">اشتراک فعال نیاز است</h1><p className="mt-3 leading-8 text-slate-600">برای استفاده از امکانات کسب‌وکار، اشتراک فعال نیاز دارید. اطلاعات قبلی شما محفوظ است.</p></>}{account?.trial_used_at && <p className="mt-4 rounded-xl bg-slate-100 p-3 text-sm text-slate-700">آزمایش رایگان استفاده شده است.</p>}{error && <p className="mt-4 rounded-xl bg-red-50 p-3 text-sm text-red-700">{error}</p>}<div className="mt-5 grid gap-3 sm:grid-cols-2"><button className="min-h-12 rounded-xl border border-slate-300 font-bold" onClick={() => navigate("/pricing")}>مشاهده تعرفه‌ها</button><button className="min-h-12 rounded-xl border border-slate-300 font-bold" onClick={() => navigate("/account/subscription")}>وضعیت اشتراک</button></div></section></main>;
}
