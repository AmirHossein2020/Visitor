import { useCallback, useEffect, useState } from "react";
import { navigate } from "../hooks/useRoute";
import OrderLayout from "../layouts/OrderLayout";
import { getErrorMessage } from "../services/api";
import { deactivateCompany, listCompanies } from "../services/companies";

export default function CompanyListPage() {
  const [profiles, setProfiles] = useState([]);
  const [search, setSearch] = useState("");
  const [error, setError] = useState("");
  const [isLoading, setIsLoading] = useState(true);
  const load = useCallback(async (term = "") => { setIsLoading(true); try { setProfiles(await listCompanies(term)); } catch (requestError) { setError(getErrorMessage(requestError)); } finally { setIsLoading(false); } }, []);
  useEffect(() => { load(); }, [load]);
  const remove = async (profile) => { if (!window.confirm("این فروشنده غیرفعال شود؟")) return; try { await deactivateCompany(profile.id); setProfiles((items) => items.filter((item) => item.id !== profile.id)); } catch (requestError) { setError(getErrorMessage(requestError)); } };
  return <OrderLayout title="فروشنده‌ها" backPath="/">
    <p className="mb-5 rounded-xl bg-teal-50 p-3 text-sm leading-6 text-teal-800">این مشخصات فقط هنگام صدور فاکتور به‌عنوان هویت فروشنده استفاده خواهند شد.</p>
    <div className="mb-5 flex flex-col gap-3 sm:flex-row"><form className="flex flex-1 gap-2" onSubmit={(event) => { event.preventDefault(); load(search.trim()); }}><input className="min-h-12 min-w-0 flex-1 rounded-xl border border-slate-300 bg-white px-4" placeholder="جستجوی نام یا شناسه" value={search} onChange={(event) => setSearch(event.target.value)} /><button className="min-h-12 rounded-xl border border-slate-300 bg-white px-4 font-semibold" type="submit">جستجو</button></form><button className="min-h-12 rounded-xl bg-teal-700 px-5 font-semibold text-white" onClick={() => navigate("/companies/new")} type="button">افزودن فروشنده</button></div>
    {error && <p className="mb-4 rounded-xl bg-red-50 p-3 text-sm text-red-700">{error}</p>}
    {isLoading ? <p className="py-12 text-center text-slate-600">در حال دریافت فروشنده‌ها…</p> : profiles.length === 0 ? <div className="rounded-2xl bg-white py-12 text-center text-slate-600 ring-1 ring-slate-200">فروشنده‌ای ثبت نشده است.</div> : <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">{profiles.map((profile) => <article className="rounded-2xl bg-white p-5 ring-1 ring-slate-200" key={profile.id}><button className="min-h-12 w-full text-right" onClick={() => navigate("/companies/" + profile.id)} type="button"><h2 className="text-lg font-bold">{profile.name}</h2>{profile.phone_number && <p className="mt-1 text-sm text-slate-500" dir="ltr">{profile.phone_number}</p>}</button><div className="mt-4 grid grid-cols-3 gap-2"><button className="min-h-11 rounded-xl border border-slate-300 text-sm font-semibold" onClick={() => navigate("/companies/" + profile.id)} type="button">مشاهده</button><button className="min-h-11 rounded-xl border border-slate-300 text-sm font-semibold" onClick={() => navigate("/companies/" + profile.id + "/edit")} type="button">ویرایش</button><button className="min-h-11 rounded-xl border border-red-200 text-sm font-semibold text-red-700" onClick={() => remove(profile)} type="button">غیرفعال</button></div></article>)}</div>}
  </OrderLayout>;
}
