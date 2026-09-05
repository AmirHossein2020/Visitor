import { useEffect, useState } from "react";
import { Badge, Button, Card, StatePanel } from "../components/ui";
import { navigate } from "../hooks/useRoute";
import { getErrorMessage } from "../services/api";
import { useAuth } from "../services/AuthContext";
import { formatPrice } from "../services/products";
import { activateFreeTrial, createSubscriptionOrder, getMySubscription, listPlans } from "../services/subscriptions";

const features = ["مدیریت مشتری و کالا", "سفارش فروش و صدور فاکتور PDF", "مهر و امضای فروشنده", "خرید، مرجوعی و موجودی", "داشبورد و گزارش‌های فروش", "دسترسی موبایل و پروفایل کسب‌وکار"];

export default function PricingPage() {
  const { user } = useAuth();
  const [plans, setPlans] = useState([]);
  const [account, setAccount] = useState(null);
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const load = () => {
    setLoading(true); setError("");
    Promise.all([listPlans(), user ? getMySubscription() : Promise.resolve(null)])
      .then(([items, state]) => { setPlans(items); setAccount(state); })
      .catch((requestError) => setError(getErrorMessage(requestError)))
      .finally(() => setLoading(false));
  };
  useEffect(load, [user]);
  useEffect(() => {
    const site = (import.meta.env.VITE_SITE_URL || window.location.origin).replace(/\/$/, "");
    document.title = "تعرفه و آزمایش رایگان ویزیتورکار";
    document.head.querySelector('meta[name="description"]')?.setAttribute("content", "مشاهده پلن‌های ماهانه و سالانه و شروع آزمایش رایگان ۲۴ ساعته نرم افزار ویزیتوری ویزیتورکار.");
    document.head.querySelector('link[rel="canonical"]')?.setAttribute("href", `${site}/pricing`);
    document.head.querySelector('meta[property="og:url"]')?.setAttribute("content", `${site}/pricing`);
  }, []);

  const select = async (id) => {
    if (!user) return navigate("/register");
    try { const order = await createSubscriptionOrder(id); navigate(`/account/subscription/orders/${order.id}/payment`); }
    catch (requestError) { setError(getErrorMessage(requestError)); }
  };
  const trial = async () => {
    if (!user) return navigate("/register");
    if (account?.is_active) return navigate("/app");
    if (!account?.trial_eligible) return navigate("/account/subscription");
    setBusy(true); setError("");
    try { await activateFreeTrial(); window.location.assign("/app"); }
    catch (requestError) { setError(getErrorMessage(requestError)); setBusy(false); }
  };

  return <main className="pricing-page">
    <nav className="public-compact-nav"><button className="brand-lockup public-brand" onClick={() => navigate("/")}><span className="brand-mark">و</span><span><b>ویزیتورکار</b><small>مدیریت فروش</small></span></button><Button variant="ghost" onClick={() => navigate(user ? "/account/profile" : "/")}>بازگشت</Button></nav>
    <div className="pricing-container">
      <header className="pricing-header"><Badge tone="brand">تعرفه شفاف؛ دسترسی کامل</Badge><h1>پلن مناسب مسیر کسب‌وکار شما</h1><p>امکانات پلن ماهانه و سالانه یکسان است؛ فقط مدت تعهد و هزینه متفاوت است. قیمت نهایی مستقیماً از سامانه محاسبه می‌شود.</p></header>
      {error && <StatePanel type="error" title="دریافت اطلاعات ناموفق بود" description={error} action={<Button onClick={load}>تلاش مجدد</Button>} />}
      <TrialCard account={account} busy={busy} onClick={trial} />
      {loading ? <StatePanel title="در حال دریافت تعرفه‌ها" description="پلن‌های فعال از سامانه دریافت می‌شوند…" /> : <div className="plan-grid">{plans.map((plan) => <PlanCard key={plan.id} plan={plan} onSelect={() => select(plan.id)} />)}</div>}
      {user && <div className="pricing-history-link"><Button variant="ghost" onClick={() => navigate("/account/subscription")}>مشاهده وضعیت و سوابق اشتراک</Button></div>}
    </div>
  </main>;
}

export function TrialCard({ account, busy, onClick }) {
  const activeTrial = account?.subscription?.source === "free_trial" && account.is_active;
  const used = account?.trial_used_at && !activeTrial;
  const label = account?.is_active ? "ورود به پنل کسب‌وکار" : used ? "مشاهده پلن‌های اشتراک" : "شروع آزمایش رایگان";
  return <Card className="pricing-trial-card"><div><div className="trial-heading"><Badge tone="brand">بدون نیاز به پرداخت</Badge><h2>قبل از خرید، خودتان امتحانش کنید</h2></div><p>۲۴ ساعت دسترسی واقعی به ثبت مشتری، کالا، سفارش، فاکتور و داشبورد؛ فقط یک‌بار برای حساب‌های واجد شرایط. پس از پایان، اطلاعات شما حذف نمی‌شود.</p>{activeTrial && <strong>آزمایش فعال · {account.subscription.hours_remaining} ساعت باقی‌مانده</strong>}{used && <strong className="trial-used">آزمایش رایگان قبلاً استفاده شده است.</strong>}<ul><li>بدون پرداخت</li><li>یک‌بار برای هر حساب</li><li>حفظ اطلاعات پس از پایان</li></ul></div><Button disabled={busy} onClick={onClick}>{busy ? "در حال فعال‌سازی…" : label}</Button></Card>;
}

export function PlanCard({ plan, onSelect }) {
  const discounted = Number(plan.discount_percent) > 0;
  const yearly = plan.billing_period === "yearly";
  return <Card className={`plan-card ${plan.is_featured ? "plan-card--featured" : ""}`}>
    <div className="plan-card-head"><div><p className="ui-eyebrow">{yearly ? "ارزش بهتر برای استفاده بلندمدت" : "شروع منعطف با تعهد کمتر"}</p><h2>{plan.name}</h2></div>{plan.is_featured && <Badge tone="brand">پیشنهاد ویژه</Badge>}</div>
    <p className="plan-description">{plan.description || "دسترسی کامل به ابزارهای فروش و مدیریت کسب‌وکار"}</p>
    <div className="plan-price">{discounted && <div><span>{formatPrice(plan.price)}</span><Badge tone="danger">{plan.discount_percent}٪ تخفیف</Badge></div>}<strong>{formatPrice(plan.final_price ?? plan.price)}</strong><p>{plan.billing_period_display} · {new Intl.NumberFormat("fa-IR").format(plan.duration_days)} روز دسترسی</p></div>
    <h3>تمام امکانات اصلی</h3><ul className="plan-features">{features.map((feature) => <li key={feature}><span>✓</span>{feature}</li>)}</ul>
    <Button onClick={onSelect}>انتخاب اشتراک {yearly ? "سالانه" : "ماهانه"}</Button>
  </Card>;
}
