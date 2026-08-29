import { apiRequest } from "./api";

export const listInventory = (search = "") => apiRequest("/inventory/" + (search ? "?search=" + encodeURIComponent(search) : ""));
export const getInventoryProduct = (id) => apiRequest("/inventory/" + id + "/");
