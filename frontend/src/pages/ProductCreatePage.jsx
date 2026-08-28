import ProductForm from "../components/ProductForm";
import { navigate } from "../hooks/useRoute";
import ProductLayout from "../layouts/ProductLayout";
import { getErrorMessage } from "../services/api";
import { createProduct } from "../services/products";

export default function ProductCreatePage() {
  const submit = async (form) => {
    try {
      await createProduct(form);
      navigate("/products", { replace: true });
    } catch (error) {
      throw getErrorMessage(error);
    }
  };
  return <ProductLayout title="افزودن محصول" showBack><div className="mx-auto max-w-xl"><ProductForm onSubmit={submit} submitLabel="ثبت محصول" /></div></ProductLayout>;
}
