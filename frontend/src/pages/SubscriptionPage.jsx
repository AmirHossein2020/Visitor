import { useEffect, useState } from "react";
import { navigate } from "../hooks/useRoute";
import { useAuth } from "../services/AuthContext";
import { formatPrice } from "../services/products";
import { formatJalaliDateTime } from "../services/jalali";
import { getMySubscription, listSubscriptionOrders } from "../services/subscriptions";

const labels = {pending:"در انتظار پرداخت",pending_review:"در انتظار بررسی",approved:"تأیید شده",rejected:"رد شده",cancelled:"لغو شده",active:"فعال",expired:"منقضی شده"};

export default function SubscriptionPage() {
  const { logout } = useAuth();
  const [account, setAccount] = useState();
  const [orders, setOrders] = useState([]);
  useEffect(() => { Promise.all([getMySubscription(), listSubscriptionOrders()]).then(([state, history]) => { setAccount(state); setOrders(history); }); }, []);
  if (!account) return <main className="grid min-h-dvh place-items-center">در حال دریافت وضعیت اشتراک…</main>;
  const subscription = account.subscription;
  const isTrial = subscription?.source === "free_trial";
  return <main className="min-h-dvh bg-slate-50 p-4 sm:p-8"><div className="mx-auto max-w-4xl"><header className="flex items-center justify-between gap-3"><div><button className="min-h-11 font-bold text-emerald-800" onClick={()=>navigate(account.is_active?"/app":"/account/profile")}>‹ بازگشت</button><h1 className="mt-2 text-3xl font-black">اشتراک و حساب</h1></div><button className="font-bold text-red-700" onClick={()=>{logout();navigate("/")}}>خروج</button></header><section className="mt-7 rounded-3xl bg-white p-6 ring-1 ring-slate-200"><span className="rounded-full bg-emerald-100 px-3 py-1 text-sm font-bold">{isTrial?"آزمایش رایگان فعال":labels[subscription?.effective_status]||"بدون اشتراک"}</span><h2 className="mt-5 text-2xl font-black">{subscription?.plan?.name||"اشتراک فعالی ندارید"}</h2>{subscription&&<dl className="mt-4 grid gap-3 text-sm sm:grid-cols-3"><div><dt>شروع</dt><dd className="font-bold">{formatJalaliDateTime(subscription.starts_at)}</dd></div><div><dt>پایان</dt><dd className="font-bold">{formatJalaliDateTime(subscription.expires_at)}</dd></div><div><dt>زمان باقی‌مانده</dt><dd className="font-bold">{isTrial?`${subscription.hours_remaining} ساعت باقی‌مانده`:`${subscription.days_remaining} روز`}</dd></div></dl>}{!subscription&&account.trial_used_at&&<p className="mt-4 rounded-xl bg-slate-100 p-3">آزمایش رایگان استفاده شده است و دوباره فعال نمی‌شود.</p>}<div className="mt-6 flex gap-3"><button className="admin-button" onClick={()=>navigate("/account/profile")}>حساب کاربری</button><button className="admin-button bg-emerald-800 text-white" onClick={()=>navigate(account.is_active?"/app":"/pricing")}>{account.is_active?"ورود به پنل":"مشاهده تعرفه‌ها"}</button></div></section><section className="mt-6"><h2 className="text-xl font-black">تاریخچه درخواست‌ها</h2><div className="mt-3 space-y-3">{orders.map(order=><article className="flex flex-wrap justify-between gap-3 rounded-2xl bg-white p-5 ring-1 ring-slate-200" key={order.id}><div><b>{order.plan.name}</b><p className="text-sm text-slate-500">{formatJalaliDateTime(order.created_at)}</p></div><div className="text-left"><p className="font-bold text-emerald-800">{formatPrice(order.amount_snapshot)}</p><p>{labels[order.latest_payment?.status||order.status]}</p>{order.status==="pending"&&<button className="mt-2 font-bold text-emerald-800" onClick={()=>navigate(`/account/subscription/orders/${order.id}/payment`)}>ثبت یا مشاهده پرداخت</button>}</div></article>)}{!orders.length&&<p className="rounded-2xl bg-white p-6 text-center">هنوز درخواست پرداختی ثبت نشده است.</p>}</div></section></div></main>;
}
