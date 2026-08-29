import { apiRequest } from "./api";

export const listCompanies = (search = "") => apiRequest("/companies/" + (search ? "?search=" + encodeURIComponent(search) : ""));
export const getCompany = (id) => apiRequest("/companies/" + id + "/");
export const createCompany = (data) => apiRequest("/companies/", { method: "POST", body: JSON.stringify(data) });
export const updateCompany = (id, data) => apiRequest("/companies/" + id + "/", { method: "PATCH", body: JSON.stringify(data) });
export const deactivateCompany = (id) => apiRequest("/companies/" + id + "/", { method: "DELETE" });
