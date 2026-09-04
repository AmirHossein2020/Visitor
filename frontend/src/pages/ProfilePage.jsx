import { useEffect, useState } from "react";
import AppShell from "../components/AppShell";
import FormField from "../components/FormField";
import { Badge, Button, Card, Icon, StatePanel } from "../components/ui";
import { navigate } from "../hooks/useRoute";
import { formatDateTime } from "../services/formatters";
import { getMyProfile, getMySubscription, listSubscriptionOrders, updateMyProfile } from "../services/subscriptions";

const labels = { pending: "در انتظار پرداخت", pending_review: "رسید ارسال شده و در انتظار بررسی", approved: "پرداخت تأیید شد", rejected: "پرداخت رد شد", cancelled: "لغو شده", active: "فعال", expired: "منقضی شده", inactive: "غیرفعال" };
const tones = { active: "success", approved: "success", pending: "warning", pending_review: "warning", rejected: "danger", cancelled: "danger", expired: "neutral", inactive: "neutral" };
const Meta = ({ label, children, ltr }) => <div className="account-meta"><dt>{label}</dt><dd dir={ltr ? "ltr" : undefined}>{children}</dd></div>;

export default function ProfilePage() {
  const [state, setState] = useState();
  const [form, setForm] = useState({ full_name: "", phone_number: "" });
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");
  const [saving, setSaving] = useState(false);

  const load = () => {
    setError("");
    return Promise.all([getMyProfile(), getMySubscription(), listSubscriptionOrders()])
      .then(([profile, account, orders]) => {
        setState({ profile, account, orders });
        setForm({ full_name: profile.full_name || "", phone_number: profile.phone_number || "" });
      }).catch(() => setError("دریافت اطلاعات حساب با خطا مواجه شد."));
  };
  useEffect(() => { load(); }, []);

  const save = async (event) => {
    event.preventDefault(); setSaving(true); setError(""); setNotice("");
    try { await updateMyProfile(form); setNotice("اطلاعات حساب ذخیره شد."); await load(); }
    catch (requestError) { setError(Object.values(requestError.data || {}).flat().join(" ") || "ذخیره اطلاعات ممکن نشد."); }
    finally { setSaving(false); }
  };

  if (!state) return <AppShell title="حساب کاربری" subtitle="اطلاعات شخصی و وضعیت دسترسی"><StatePanel type={error ? "error" : "loading"} title={error || "در حال دریافت حساب کاربری"} action={error && <Button onClick={load}>تلاش مجدد</Button>} /></AppShell>;

  const { profile, account, orders } = state;
  const subscription = account.subscription;
  const latest = orders[0];
  const payment = latest?.latest_payment;
  const status = subscription?.effective_status || payment?.status || latest?.status || "inactive";

  return <AppShell
    title="حساب کاربری"
    subtitle="اطلاعات شخصی، حساب و دسترسی شما"
    backPath="/app"
    action={<Button variant="secondary" onClick={() => navigate("/account/subscription")}><span className="label-short">اشتراک</span><span className="label-wide">اشتراک و پرداخت‌ها</span></Button>}
  >
    <div className="account-page">
      {error && <StatePanel type="error" title="انجام عملیات ممکن نشد" description={error} />}
      {notice && <div className="account-notice" role="status">{notice}</div>}
      <section className="account-overview">
        <div className="account-avatar"><Icon name="user" className="size-7" /></div>
        <div><p className="ui-eyebrow">پروفایل شخصی</p><h2>{profile.full_name}</h2><p dir="ltr">{profile.email}</p></div>
        <Badge tone={profile.is_active ? "success" : "neutral"}>{profile.is_active ? "حساب فعال" : "حساب غیرفعال"}</Badge>
      </section>

      <div className="account-grid">
        <Card>
          <div className="profile-section-title"><p className="ui-eyebrow">اطلاعات شخصی</p><h3>مشخصات قابل ویرایش</h3></div>
          <form className="account-form" onSubmit={save}>
            <FormField id="profile_name" label="نام و نام خانوادگی" required value={form.full_name} onChange={(event) => setForm({ ...form, full_name: event.target.value })} />
            <FormField id="profile_phone" label="شماره تماس (اختیاری)" inputMode="tel" value={form.phone_number} onChange={(event) => setForm({ ...form, phone_number: event.target.value })} />
            <Button disabled={saving}>{saving ? "در حال ذخیره…" : "ذخیره اطلاعات"}</Button>
          </form>
        </Card>

        <Card>
          <div className="profile-section-title"><p className="ui-eyebrow">اطلاعات حساب</p><h3>عضویت و وضعیت حساب</h3></div>
          <dl className="account-meta-grid">
            <Meta label="ایمیل" ltr>{profile.email}</Meta>
            <Meta label="تاریخ ثبت‌نام">{formatDateTime(profile.date_joined)}</Meta>
            <Meta label="وضعیت حساب"><Badge tone={profile.is_active ? "success" : "neutral"}>{profile.is_active ? "فعال" : "غیرفعال"}</Badge></Meta>
          </dl>
        </Card>
      </div>

      <Card className="subscription-summary">
        <div className="subscription-summary-head"><div><p className="ui-eyebrow">خلاصه اشتراک</p><h3>{subscription?.plan?.name || "اشتراک فعالی ندارید"}</h3></div><Badge tone={tones[status] || "neutral"}>{labels[status] || status}</Badge></div>
        {subscription ? <dl className="summary-stats">
          <Meta label="نوع دسترسی">{subscription.source === "free_trial" ? "آزمایش رایگان" : subscription.plan.billing_period === "yearly" ? "اشتراک سالانه" : "اشتراک ماهانه"}</Meta>
          <Meta label="شروع">{formatDateTime(subscription.starts_at)}</Meta>
          <Meta label="انقضا">{formatDateTime(subscription.expires_at)}</Meta>
          <Meta label="زمان باقی‌مانده">{subscription.source === "free_trial" ? `${subscription.hours_remaining} ساعت` : subscription.effective_status === "active" ? `${subscription.days_remaining} روز` : "منقضی شده"}</Meta>
        </dl> : latest && <div className="pending-subscription"><p>{labels[payment?.status] || labels[latest.status]}</p>{payment?.admin_note && <p>دلیل رد: {payment.admin_note}</p>}</div>}
        <div className="summary-actions"><Button onClick={() => navigate(subscription?.effective_status === "active" ? "/account/subscription" : "/pricing")}>{subscription?.effective_status === "active" ? "مشاهده جزئیات اشتراک" : "مشاهده پلن‌ها"}</Button>{account.is_active && <Button variant="ghost" onClick={() => navigate("/app")}>بازگشت به پنل</Button>}</div>
      </Card>
    </div>
  </AppShell>;
}
