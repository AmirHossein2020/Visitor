import { apiBlob, apiRequest } from "./api";
import { normalizePhone } from "./normalization";

export const listCompanies = (search = "") => apiRequest("/companies/" + (search ? "?search=" + encodeURIComponent(search) : ""));
export const getCompany = (id) => apiRequest("/companies/" + id + "/");
const body = data => {
  if (data instanceof FormData) {
    if (data.has("phone_number")) data.set("phone_number", normalizePhone(data.get("phone_number")));
    return data;
  }
  return JSON.stringify({ ...data, phone_number: normalizePhone(data.phone_number) });
};
export const createCompany = (data) => apiRequest("/companies/", { method: "POST", body: body(data) });
export const updateCompany = (id, data) => apiRequest("/companies/" + id + "/", { method: "PATCH", body: body(data) });
export const deactivateCompany = (id) => apiRequest("/companies/" + id + "/", { method: "DELETE" });
export const companyAsset = (id, kind) => apiBlob(`/companies/${id}/${kind}/`);
export const removeCompanyAsset = (id, kind) => apiRequest(`/companies/${id}/${kind}/`, { method: "DELETE" });
