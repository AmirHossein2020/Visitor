import CustomerForm from "../components/CustomerForm";
import { navigate } from "../hooks/useRoute";
import CustomerLayout from "../layouts/CustomerLayout";
import { getErrorMessage } from "../services/api";
import { createCustomer } from "../services/customers";

export default function CustomerCreatePage() {
  const submit = async (form) => {
    try { await createCustomer(form); navigate("/customers", { replace: true }); }
    catch (error) { throw getErrorMessage(error); }
  };
  return <CustomerLayout title="افزودن مشتری" showBack><div className="mx-auto max-w-xl"><CustomerForm onSubmit={submit} submitLabel="ثبت مشتری" /></div></CustomerLayout>;
}
