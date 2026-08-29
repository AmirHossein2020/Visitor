import { useEffect, useState } from "react";
import { navigate } from "../hooks/useRoute";
import OrderLayout from "../layouts/OrderLayout";
import { getErrorMessage } from "../services/api";
import { getCompany } from "../services/companies";

const Detail = ({ label, value }) => value ? <div><dt className="text-sm text-slate-500">{label}</dt><dd className="mt-1 whitespace-pre-wrap font-medium">{value}</dd></div> : null;

export default function CompanyDetailPage({ companyId }) {
  const [profile, setProfile] = useState(null);
  const [error, setError] = useState("");
  useEffect(() => { getCompany(companyId).then(setProfile).catch((requestError) => setError(getErrorMessage(requestError))); }, [companyId]);
  return <OrderLayout title="اطلاعات فروشنده" backPath="/companies"><div className="mx-auto max-w-2xl">{error && <p className="rounded-xl bg-red-50 p-3 text-sm text-red-700">{error}</p>}{!error && !profile && <p className="py-12 text-center text-slate-600">در حال دریافت اطلاعات…</p>}{profile && <section className="rounded-2xl bg-white p-5 ring-1 ring-slate-200 sm:p-7"><div className="flex items-start justify-between gap-3"><div><p className="text-sm text-teal-700">هویت فروشنده برای صدور فاکتور</p><h2 className="mt-1 text-xl font-bold">{profile.name}</h2></div><button className="min-h-11 rounded-xl border border-slate-300 px-4 font-semibold" onClick={() => navigate("/companies/" + profile.id + "/edit")} type="button">ویرایش</button></div><dl className="mt-7 grid gap-5 sm:grid-cols-2"><Detail label="شماره تماس" value={profile.phone_number} /><Detail label="کد اقتصادی" value={profile.economic_code} /><Detail label="شناسه ملی" value={profile.national_id} /><Detail label="شماره ثبت" value={profile.registration_number} /><Detail label="کد پستی" value={profile.postal_code} /><Detail label="نشانی" value={profile.address} /><Detail label="توضیحات" value={profile.description} /></dl></section>}</div></OrderLayout>;
}
