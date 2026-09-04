import { useEffect, useState } from "react";
import AppShell from "../components/AppShell";
import { Badge, Button, Card, StatePanel } from "../components/ui";
import { navigate } from "../hooks/useRoute";
import { formatJalaliDateTime } from "../services/jalali";
import { formatPrice } from "../services/products";
import { getMySubscription, listSubscriptionOrders } from "../services/subscriptions";

const labels = { pending: "در انتظار پرداخت", pending_review: "در انتظار بررسی", approved: "تأیید شده", rejected: "رد شده", cancelled: "لغو شده", active: "فعال", expired: "منقضی شده" };
const tones = { pending: "warning", pending_review: "warning", approved: "success", active: "success", rejected: "danger", cancelled: "danger", expired: "neutral" };
const Info = ({ label, children }) => <div className="subscription-info"><dt>{label}</dt><dd>{children}</dd></div>;

export default function SubscriptionPage() {
  const [account, setAccount] = useState();
  const [orders, setOrders] = useState([]);
  const [error, setError] = useState("");
  const load = () => {
    setError("");
    Promise.all([getMySubscription(), listSubscriptionOrders()])
      .then(([state, history]) => { setAccount(state); setOrders(history); })
      .catch(() => setError("دریافت وضعیت اشتراک ممکن نشد."));
  };
  useEffect(load, []);

  if (!account) return <AppShell title="اشتراک" subtitle="مدیریت دسترسی و پرداخت‌ها" backPath="/account/profile"><StatePanel type={error ? "error" : "loading"} title={error || "در حال دریافت وضعیت اشتراک"} action={error && <Button onClick={load}>تلاش مجدد</Button>} /></AppShell>;

  const subscription = account.subscription;
  const isTrial = subscription?.source === "free_trial";
  const status = subscription?.effective_status || "expired";
  const trialState = isTrial && account.is_active ? "active" : account.trial_eligible ? "eligible" : account.trial_used_at ? "used" : "ineligible";
  const trialLabels = { active: "آزمایش فعال", eligible: "واجد شرایط", used: "استفاده شده", ineligible: "غیرفعال" };

  return <AppShell
    title="اشتراک و پرداخت‌ها"
    subtitle="وضعیت دسترسی، اعتبار و درخواست‌های پرداخت"
    backPath="/account/profile"
    action={<Button onClick={() => navigate(account.is_active ? "/app" : "/pricing")}><span className="label-short">{account.is_active ? "پنل" : "پلن‌ها"}</span><span className="label-wide">{account.is_active ? "ورود به پنل" : "مشاهده پلن‌ها"}</span></Button>}
  >
    <div className="subscription-page">
      <Card className="current-plan-card">
        <div className="current-plan-main">
          <div><p className="ui-eyebrow">اشتراک فعلی</p><div className="current-plan-title"><h2>{subscription?.plan?.name || "بدون اشتراک فعال"}</h2><Badge tone={tones[status]}>{subscription ? labels[status] : "غیرفعال"}</Badge></div><p>{isTrial ? "دسترسی آزمایشی یک‌روزه" : subscription ? subscription.plan.billing_period === "yearly" ? "اشتراک پرداختی سالانه" : "اشتراک پرداختی ماهانه" : "برای ادامه استفاده یکی از پلن‌ها را انتخاب کنید."}</p></div>
          <div className="remaining-time"><span>زمان باقی‌مانده</span><strong>{subscription ? isTrial ? `${subscription.hours_remaining} ساعت` : `${subscription.days_remaining} روز` : "—"}</strong></div>
        </div>
        {subscription && <dl className="subscription-info-grid"><Info label="نوع / منبع">{isTrial ? "آزمایش رایگان" : "پرداخت دستی"}</Info><Info label="شروع">{formatJalaliDateTime(subscription.starts_at)}</Info><Info label="تاریخ انقضا">{formatJalaliDateTime(subscription.expires_at)}</Info></dl>}
        <div className="summary-actions"><Button onClick={() => navigate("/pricing")}>{subscription && account.is_active ? "تمدید یا تغییر پلن" : "انتخاب اشتراک"}</Button><Button variant="ghost" onClick={() => navigate("/account/profile")}>حساب کاربری</Button></div>
      </Card>

      <Card className={`trial-status trial-status--${trialState}`}>
        <div><div className="trial-status-title"><p className="ui-eyebrow">آزمایش رایگان</p><Badge tone={trialState === "active" ? "success" : trialState === "eligible" ? "brand" : "neutral"}>{trialLabels[trialState]}</Badge></div><h3>یک روز دسترسی واقعی به پنل کسب‌وکار</h3><p>{trialState === "eligible" ? "بدون پرداخت، فقط یک‌بار و با حفظ اطلاعات پس از پایان اعتبار." : trialState === "active" ? `${subscription.hours_remaining} ساعت از زمان آزمایش باقی مانده است.` : "آزمایش رایگان این حساب قبلاً استفاده شده یا در دسترس نیست."}</p></div>
        {trialState === "eligible" && <Button variant="secondary" onClick={() => navigate("/pricing")}>مشاهده شرایط آزمایش</Button>}
      </Card>

      <section className="subscription-history">
        <div className="section-heading"><div><p className="ui-eyebrow">سوابق مالی</p><h2>درخواست‌های اشتراک</h2></div></div>
        <div className="history-list">
          {orders.map((order) => {
            const orderStatus = order.latest_payment?.status || order.status;
            return <Card className="history-item" key={order.id}><div><strong>{order.plan.name}</strong><span>{formatJalaliDateTime(order.created_at)}</span></div><div><b>{formatPrice(order.amount_snapshot)}</b><Badge tone={tones[orderStatus] || "neutral"}>{labels[orderStatus]}</Badge>{order.status === "pending" && <Button variant="ghost" onClick={() => navigate(`/account/subscription/orders/${order.id}/payment`)}>ثبت یا مشاهده پرداخت</Button>}</div></Card>;
          })}
          {!orders.length && <StatePanel type="empty" title="هنوز درخواست پرداختی ثبت نشده است" description="پس از انتخاب پلن، درخواست شما در این بخش نمایش داده می‌شود." action={<Button onClick={() => navigate("/pricing")}>مشاهده پلن‌ها</Button>} />}
        </div>
      </section>
    </div>
  </AppShell>;
}
