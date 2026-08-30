import { apiRequest } from "./api";
import { formatMoney } from "./formatters";

export const units = [
  { value: "item", label: "عدد" },
  { value: "package", label: "بسته" },
  { value: "carton", label: "کارتن" },
  { value: "kilogram", label: "کیلوگرم" },
  { value: "gram", label: "گرم" },
  { value: "liter", label: "لیتر" },
  { value: "meter", label: "متر" },
  { value: "other", label: "سایر" },
];

export const listProducts = (search = "") =>
  apiRequest("/products/" + (search ? "?search=" + encodeURIComponent(search) : ""));

export const getProduct = (id) => apiRequest("/products/" + id + "/");

export const createProduct = (data) =>
  apiRequest("/products/", { method: "POST", body: JSON.stringify(data) });

export const updateProduct = (id, data) =>
  apiRequest("/products/" + id + "/", { method: "PATCH", body: JSON.stringify(data) });

export const deactivateProduct = (id) =>
  apiRequest("/products/" + id + "/", { method: "DELETE" });

export function formatPrice(value) {
  return formatMoney(value);
}
