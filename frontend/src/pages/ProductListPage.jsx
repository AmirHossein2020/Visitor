import { useCallback, useEffect, useState } from "react";
import ProductLayout from "../layouts/ProductLayout";
import { navigate } from "../hooks/useRoute";
import { deactivateProduct, formatPrice, listProducts } from "../services/products";
import { getErrorMessage } from "../services/api";

export default function ProductListPage() {
  const [products, setProducts] = useState([]);
  const [search, setSearch] = useState("");
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState("");

  const loadProducts = useCallback(async (term = "") => {
    setIsLoading(true);
    setError("");
    try {
      setProducts(await listProducts(term));
    } catch (requestError) {
      setError(getErrorMessage(requestError));
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => { loadProducts(); }, [loadProducts]);

  const submitSearch = (event) => {
    event.preventDefault();
    loadProducts(search.trim());
  };

  const remove = async (product) => {
    if (!window.confirm("این محصول غیرفعال شود؟")) return;
    try {
      await deactivateProduct(product.id);
      setProducts((items) => items.filter((item) => item.id !== product.id));
    } catch (requestError) {
      setError(getErrorMessage(requestError));
    }
  };

  return (
    <ProductLayout title="محصولات">
      <div className="mb-5 flex flex-col gap-3 sm:flex-row">
        <form className="flex flex-1 gap-2" onSubmit={submitSearch}>
          <input aria-label="جستجوی محصول" className="min-h-12 min-w-0 flex-1 rounded-xl border border-slate-300 bg-white px-4 outline-none focus:border-teal-600 focus:ring-2 focus:ring-teal-100" placeholder="جستجو در نام یا برند" value={search} onChange={(event) => setSearch(event.target.value)} />
          <button className="min-h-12 rounded-xl border border-slate-300 bg-white px-4 font-semibold text-slate-700 hover:bg-slate-50" type="submit">جستجو</button>
        </form>
        <button className="min-h-12 rounded-xl bg-teal-700 px-5 font-semibold text-white hover:bg-teal-800" onClick={() => navigate("/products/new")} type="button">افزودن محصول</button>
      </div>
      {error && <p className="mb-4 rounded-xl bg-red-50 px-3 py-2 text-sm text-red-700" role="alert">{error}</p>}
      {isLoading ? (
        <p className="py-12 text-center text-slate-600">در حال دریافت محصولات…</p>
      ) : products.length === 0 ? (
        <div className="rounded-2xl bg-white px-5 py-12 text-center text-slate-600 ring-1 ring-slate-200">محصولی پیدا نشد.</div>
      ) : (
        <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
          {products.map((product) => (
            <article className="rounded-2xl bg-white p-5 shadow-sm ring-1 ring-slate-200" key={product.id}>
              <h2 className="text-lg font-bold text-slate-900">{product.name}</h2>
              <p className="mt-1 min-h-6 text-sm text-slate-500">{product.brand || "بدون برند"}</p>
              <p className="mt-4 font-semibold text-teal-800">{formatPrice(product.default_price)}</p>
              <p className="mt-1 text-sm text-slate-600">واحد: {product.unit_display}</p>
              <div className="mt-5 grid grid-cols-2 gap-2">
                <button className="min-h-11 rounded-xl border border-slate-300 font-semibold text-slate-700 hover:bg-slate-50" onClick={() => navigate("/products/" + product.id + "/edit")} type="button">ویرایش</button>
                <button className="min-h-11 rounded-xl border border-red-200 font-semibold text-red-700 hover:bg-red-50" onClick={() => remove(product)} type="button">غیرفعال‌سازی</button>
              </div>
            </article>
          ))}
        </div>
      )}
    </ProductLayout>
  );
}
