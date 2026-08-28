import { apiRequest } from "./api";

export const listCustomers = (search = "") =>
  apiRequest("/customers/" + (search ? "?search=" + encodeURIComponent(search) : ""));
export const getCustomer = (id) => apiRequest("/customers/" + id + "/");
export const createCustomer = (data) =>
  apiRequest("/customers/", { method: "POST", body: JSON.stringify(data) });
export const updateCustomer = (id, data) =>
  apiRequest("/customers/" + id + "/", { method: "PATCH", body: JSON.stringify(data) });
export const deactivateCustomer = (id) =>
  apiRequest("/customers/" + id + "/", { method: "DELETE" });
