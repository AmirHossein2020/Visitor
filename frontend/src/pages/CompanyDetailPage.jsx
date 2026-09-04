import { useEffect, useState } from "react";
import { navigate } from "../hooks/useRoute";
import OrderLayout from "../layouts/OrderLayout";
import { getErrorMessage } from "../services/api";
import { companyAsset, getCompany } from "../services/companies";

const Detail = ({ label, value }) => value ? <div><dt className="text-sm text-slate-500">{label}</dt><dd className="mt-1 whitespace-pre-wrap font-medium">{value}</dd></div> : null;

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
  return <div className="rounded-xl bg-white/70 p-3 ring-1 ring-slate-200">
    <p className="font-bold">{label}</p>
    {url && <div className="mt-3 rounded-lg bg-slate-200 p-2"><img alt={`پیش‌نمایش پردازش‌شده ${label}`} className="h-28 w-full object-contain" src={url} /></div>}
  </div>;
}

export default function CompanyDetailPage({ companyId }) {
  const [profile, setProfile] = useState(null);
  const [error, setError] = useState("");
  useEffect(() => { getCompany(companyId).then(setProfile).catch((requestError) => setError(getErrorMessage(requestError))); }, [companyId]);
  return <OrderLayout title="اطلاعات فروشنده" backPath="/companies"><div className="mx-auto max-w-2xl">{error && <p className="rounded-xl bg-red-50 p-3 text-sm text-red-700">{error}</p>}{!error && !profile && <p className="py-12 text-center text-slate-600">در حال دریافت اطلاعات…</p>}{profile && <section className="rounded-2xl bg-white p-5 ring-1 ring-slate-200 sm:p-7"><div className="flex items-start justify-between gap-3"><div><p className="text-sm text-teal-700">هویت فروشنده برای صدور فاکتور</p><h2 className="mt-1 text-xl font-bold">{profile.name}</h2></div><button className="min-h-11 rounded-xl border border-slate-300 px-4 font-semibold" onClick={() => navigate("/companies/" + profile.id + "/edit")} type="button">ویرایش</button></div><dl className="mt-7 grid gap-5 sm:grid-cols-2"><Detail label="شماره تماس" value={profile.phone_number} /><Detail label="کد اقتصادی" value={profile.economic_code} /><Detail label="شناسه ملی" value={profile.national_id} /><Detail label="شماره ثبت" value={profile.registration_number} /><Detail label="کد پستی" value={profile.postal_code} /><Detail label="نشانی" value={profile.address} /><Detail label="توضیحات" value={profile.description} /></dl>{(profile.has_stamp || profile.has_signature) && <div className="mt-7 rounded-2xl bg-slate-50 p-4"><p className="text-sm font-bold text-teal-800">پس‌زمینه تصویر به‌صورت خودکار حذف شد.</p><div className="mt-3 grid gap-4 sm:grid-cols-2">{profile.has_stamp && <ProcessedAsset companyId={profile.id} kind="stamp" label="مهر" />}{profile.has_signature && <ProcessedAsset companyId={profile.id} kind="signature" label="امضا" />}</div></div>}</section>}</div></OrderLayout>;
}
