import { useEffect, useState } from "react";
import { Badge, Button, Card, StatePanel } from "../components/ui";
import { navigate } from "../hooks/useRoute";
import OrderLayout from "../layouts/OrderLayout";
import { getErrorMessage } from "../services/api";
import { companyAsset, getCompany } from "../services/companies";

const Detail = ({ label, value, wide = false }) => (
  <div className={`profile-detail ${wide ? "profile-detail--wide" : ""}`}>
    <dt>{label}</dt>
    <dd>{value || "ثبت نشده"}</dd>
  </div>
);

function ProcessedAsset({ companyId, kind, label }) {
  const [url, setUrl] = useState("");
  useEffect(() => {
    let objectUrl = "";
    companyAsset(companyId, kind).then((blob) => {
      objectUrl = URL.createObjectURL(blob);
      setUrl(objectUrl);
    }).catch(() => {});
    return () => { if (objectUrl) URL.revokeObjectURL(objectUrl); };
  }, [companyId, kind]);

  return <div className="identity-asset">
    <div><strong>{label}</strong><span>نسخه پردازش‌شده برای فاکتور</span></div>
    {url ? <img alt={`پیش‌نمایش ${label} فروشنده`} src={url} /> : <span className="asset-placeholder">در حال دریافت…</span>}
  </div>;
}

export default function CompanyDetailPage({ companyId }) {
  const [profile, setProfile] = useState(null);
  const [error, setError] = useState("");
  useEffect(() => {
    getCompany(companyId).then(setProfile).catch((requestError) => setError(getErrorMessage(requestError)));
  }, [companyId]);

  return <OrderLayout
    title="پروفایل فروشنده"
    subtitle="هویت مورد استفاده در صدور فاکتور"
    backPath="/companies"
    action={profile && <Button onClick={() => navigate(`/companies/${profile.id}/edit`)}>ویرایش اطلاعات</Button>}
  >
    <div className="company-profile-page">
      {error && <StatePanel type="error" title="دریافت پروفایل ناموفق بود" description={error} />}
      {!error && !profile && <StatePanel title="در حال دریافت اطلاعات فروشنده" />}
      {profile && <>
        <section className="company-identity-hero">
          <div className="company-monogram">{profile.name.trim().slice(0, 1)}</div>
          <div><Badge tone={profile.is_active ? "success" : "neutral"}>{profile.is_active ? "فعال" : "غیرفعال"}</Badge><h2>{profile.name}</h2><p>این مشخصات هنگام صدور فاکتور به‌عنوان هویت فروشنده استفاده می‌شود.</p></div>
        </section>

        <div className="company-profile-grid">
          <Card>
            <div className="profile-section-title"><p className="ui-eyebrow">اطلاعات اصلی</p><h3>ارتباط و نشانی</h3></div>
            <dl className="profile-details">
              <Detail label="شماره تماس" value={profile.phone_number} />
              <Detail label="کد پستی" value={profile.postal_code} />
              <Detail label="نشانی" value={profile.address} wide />
            </dl>
          </Card>
          <Card>
            <div className="profile-section-title"><p className="ui-eyebrow">اطلاعات ثبتی</p><h3>شناسه‌های صورتحساب</h3></div>
            <dl className="profile-details">
              <Detail label="کد اقتصادی" value={profile.economic_code} />
              <Detail label="شناسه ملی" value={profile.national_id} />
              <Detail label="شماره ثبت" value={profile.registration_number} />
            </dl>
          </Card>
        </div>

        <Card className="profile-assets-card">
          <div className="profile-section-title"><p className="ui-eyebrow">اسناد تصویری</p><h3>مهر و امضا</h3><span>پس‌زمینه تصاویر به‌صورت خودکار حذف شده و نسخه آماده چاپ نمایش داده می‌شود.</span></div>
          <div className="profile-assets">
            <div className="identity-asset identity-asset--empty"><div><strong>نشان تجاری</strong><span>برای نمایش هویت بصری کسب‌وکار</span></div><span className="asset-placeholder">نشانی ثبت نشده است</span></div>
            {profile.has_stamp && <ProcessedAsset companyId={profile.id} kind="stamp" label="مهر فروشنده" />}
            {profile.has_signature && <ProcessedAsset companyId={profile.id} kind="signature" label="امضای فروشنده" />}
            {!profile.has_stamp && !profile.has_signature && <div className="empty-assets">هنوز مهر یا امضایی برای این فروشنده ثبت نشده است.</div>}
          </div>
        </Card>

        {profile.description && <Card className="profile-note"><p className="ui-eyebrow">یادداشت</p><p>{profile.description}</p></Card>}
      </>}
    </div>
  </OrderLayout>;
}
