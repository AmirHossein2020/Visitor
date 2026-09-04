import { useEffect, useState } from "react";
import AppShell from "../components/AppShell";
import { Badge, Button, Card, Icon, StatePanel } from "../components/ui";
import { navigate } from "../hooks/useRoute";
import { useAuth } from "../services/AuthContext";
import { gregorianToJalali, jalaliMonthRange, jalaliMonthTitle, todayIso } from "../services/jalali";
import { formatPrice } from "../services/products";
import { getDashboard } from "../services/reports";

const current = gregorianToJalali(todayIso());
const number = (value) => new Intl.NumberFormat("fa-IR").format(value || 0);

function validateDashboard(data) {
  const month = data?.current_month;
  if ([month?.sales_total, month?.net_sales, month?.orders_count].some((value) => value == null)) throw new Error();
  return data;
}

const MetricCard = ({ label, value, tone = "brand", hint }) => (
  <Card className="dashboard-metric">
    <div className={`metric-mark metric-mark--${tone}`} aria-hidden="true" />
    <p className="ui-eyebrow">{label}</p>
    <p className="metric-value">{formatPrice(value)}</p>
    <p className="metric-hint">{hint}</p>
  </Card>
);

export default function HomePage() {
  const { user } = useAuth();
  const [month, setMonth] = useState({ year: current.year, month: current.month });
  const [dashboard, setDashboard] = useState();
  const [error, setError] = useState("");
  const range = jalaliMonthRange(month.year, month.month);
  const isCurrent = month.year === current.year && month.month === current.month;

  const load = () => {
    setError("");
    setDashboard();
    getDashboard(range.from, range.to)
      .then(validateDashboard)
      .then(setDashboard)
      .catch(() => setError("اطلاعات فروش داشبورد کامل دریافت نشد. دوباره تلاش کنید."));
  };

  useEffect(load, [month.year, month.month]);

  const move = (delta) => setMonth((value) => {
    let nextMonth = value.month + delta;
    let year = value.year;
    if (nextMonth < 1) { nextMonth = 12; year -= 1; }
    if (nextMonth > 12) { nextMonth = 1; year += 1; }
    return year > current.year || (year === current.year && nextMonth > current.month)
      ? value
      : { year, month: nextMonth };
  });

  const metrics = dashboard?.current_month;
  const empty = metrics && ["orders_count", "invoices_count", "purchases_count", "returns_count"]
    .every((key) => metrics[key] === 0);

  return (
    <AppShell
      title="داشبورد"
      subtitle="تصویر روشن از وضعیت کسب‌وکار شما"
      action={<Button onClick={() => navigate("/customers")}><Icon name="plus" /> ثبت فروش جدید</Button>}
    >
      <section className="dashboard-welcome">
        <div>
          <Badge tone="brand">امروز در کسب‌وکار شما</Badge>
          <h2>سلام {user?.full_name || "همراه عزیز"}</h2>
          <p>فروش، خرید و فعالیت‌های ماه را سریع مرور کنید و کار بعدی را شروع کنید.</p>
        </div>
        <div className="dashboard-month" aria-label="انتخاب ماه گزارش">
          <Button variant="secondary" onClick={() => move(-1)}>ماه قبل</Button>
          <div><span>گزارش ماه</span><strong>{jalaliMonthTitle(month.year, month.month)}</strong></div>
          <Button variant="secondary" disabled={isCurrent} onClick={() => move(1)}>ماه بعد</Button>
          {!isCurrent && <button className="month-current" onClick={() => setMonth(current)}>بازگشت به ماه جاری</button>}
        </div>
      </section>

      {error && <StatePanel type="error" title="دریافت گزارش ناموفق بود" description={error} action={<Button onClick={load}>تلاش مجدد</Button>} />}
      {!dashboard && !error && <StatePanel title="در حال آماده‌سازی گزارش" description="چند لحظه صبر کنید…" />}
      {empty && <StatePanel title="این ماه هنوز فعالیتی ثبت نشده است" description="اطلاعات ماه‌های قبل محفوظ است و می‌توانید از بالای صفحه ماه را تغییر دهید." />}

      {metrics && <>
        <section className="dashboard-metrics" aria-label="شاخص‌های مالی">
          <MetricCard label="فروش" value={metrics.sales_total} hint="مجموع فروش ثبت‌شده" />
          <MetricCard label="فروش خالص" value={metrics.net_sales} tone="success" hint="پس از کسر مرجوعی" />
          <MetricCard label="خرید" value={metrics.purchase_total} tone="neutral" hint="مجموع خرید ثبت‌شده" />
          <MetricCard label="مرجوعی" value={metrics.return_total} tone="warning" hint="ارزش اقلام برگشتی" />
        </section>

        <section className="dashboard-grid">
          <Card className="activity-card">
            <div className="section-heading"><div><p className="ui-eyebrow">فعالیت این ماه</p><h2>جریان اسناد</h2></div><Badge>{jalaliMonthTitle(month.year, month.month)}</Badge></div>
            <div className="activity-list">
              {[
                ["سفارش‌ها", "orders", metrics.orders_count, "/orders"],
                ["فاکتورها", "invoice", metrics.invoices_count, "/invoices"],
                ["خریدها", "box", metrics.purchases_count, "/purchases"],
                ["مرجوعی‌ها", "back", metrics.returns_count, "/returns"],
              ].map(([label, icon, value, path]) => <button key={path} onClick={() => navigate(path)}><span className="activity-icon"><Icon name={icon} /></span><span>{label}</span><strong>{number(value)}</strong></button>)}
            </div>
          </Card>

          <Card className="quick-actions">
            <div className="section-heading"><div><p className="ui-eyebrow">دسترسی سریع</p><h2>کارهای پرکاربرد</h2></div></div>
            <div className="quick-action-grid">
              {[
                ["مشتری جدید", "users", "/customers/new"],
                ["محصول جدید", "box", "/products/new"],
                ["مشاهده موجودی", "chart", "/inventory"],
                ["گزارش‌ها", "chart", "/reports"],
                ["پشتیبانی", "support", "/support"],
              ].map(([label, icon, path]) => <button key={path} onClick={() => navigate(path)}><Icon name={icon} /><span>{label}</span></button>)}
            </div>
          </Card>
        </section>
      </>}
    </AppShell>
  );
}
