import { apiRequest } from "./api";
import { normalizePhone } from "./normalization";

const normalized = data => ({ ...data, phone_number: normalizePhone(data.phone_number) });

export const listCustomers = (search = "") =>
  apiRequest("/customers/" + (search ? "?search=" + encodeURIComponent(search) : ""));
export const getCustomer = (id) => apiRequest("/customers/" + id + "/");
export const createCustomer = (data) =>
  apiRequest("/customers/", { method: "POST", body: JSON.stringify(normalized(data)) });
export const updateCustomer = (id, data) =>
  apiRequest("/customers/" + id + "/", { method: "PATCH", body: JSON.stringify(normalized(data)) });
export const deactivateCustomer = (id) =>
  apiRequest("/customers/" + id + "/", { method: "DELETE" });
