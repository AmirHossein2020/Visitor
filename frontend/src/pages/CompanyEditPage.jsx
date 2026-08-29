import { useEffect, useState } from "react";
import SellerProfileForm from "../components/SellerProfileForm";
import { navigate } from "../hooks/useRoute";
import OrderLayout from "../layouts/OrderLayout";
import { getErrorMessage } from "../services/api";
import { getCompany, updateCompany } from "../services/companies";

export default function CompanyEditPage({ companyId }) {
  const [profile, setProfile] = useState(null);
  const [error, setError] = useState("");
  useEffect(() => { getCompany(companyId).then(setProfile).catch((requestError) => setError(getErrorMessage(requestError))); }, [companyId]);
  const submit = async (form) => { try { await updateCompany(companyId, form); navigate("/companies/" + companyId, { replace: true }); } catch (requestError) { throw getErrorMessage(requestError); } };
  return <OrderLayout title="ویرایش فروشنده" backPath="/companies"><div className="mx-auto max-w-xl">{error && <p className="rounded-xl bg-red-50 p-3 text-sm text-red-700">{error}</p>}{!error && !profile && <p className="py-12 text-center text-slate-600">در حال دریافت اطلاعات…</p>}{profile && <SellerProfileForm initialValue={profile} onSubmit={submit} submitLabel="ذخیره تغییرات" />}</div></OrderLayout>;
}
