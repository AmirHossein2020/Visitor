import SellerProfileForm from "../components/SellerProfileForm";
import { navigate } from "../hooks/useRoute";
import OrderLayout from "../layouts/OrderLayout";
import { getErrorMessage } from "../services/api";
import { createCompany } from "../services/companies";

export default function CompanyCreatePage() {
  const submit = async (form) => { try { await createCompany(form); navigate("/companies", { replace: true }); } catch (error) { throw getErrorMessage(error); } };
  return <OrderLayout title="افزودن فروشنده" backPath="/companies"><div className="mx-auto max-w-xl"><SellerProfileForm onSubmit={submit} submitLabel="ثبت فروشنده" /></div></OrderLayout>;
}
