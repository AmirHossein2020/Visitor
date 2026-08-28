import { useEffect, useState } from "react";
import ProductForm from "../components/ProductForm";
import { navigate } from "../hooks/useRoute";
import ProductLayout from "../layouts/ProductLayout";
import { getErrorMessage } from "../services/api";
import { getProduct, updateProduct } from "../services/products";

export default function ProductEditPage({ productId }) {
  const [product, setProduct] = useState(null);
  const [error, setError] = useState("");

  useEffect(() => {
    getProduct(productId).then(setProduct).catch((requestError) => setError(getErrorMessage(requestError)));
  }, [productId]);

  const submit = async (form) => {
    try {
      await updateProduct(productId, form);
      navigate("/products", { replace: true });
    } catch (requestError) {
      throw getErrorMessage(requestError);
    }
  };

  return (
    <ProductLayout title="ویرایش محصول" showBack>
      <div className="mx-auto max-w-xl">
        {error && <p className="rounded-xl bg-red-50 px-3 py-3 text-sm text-red-700" role="alert">{error}</p>}
        {!error && !product && <p className="py-12 text-center text-slate-600">در حال دریافت محصول…</p>}
        {product && <ProductForm initialValue={product} onSubmit={submit} submitLabel="ذخیره تغییرات" />}
      </div>
    </ProductLayout>
  );
}
