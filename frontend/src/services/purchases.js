import { apiRequest } from "./api";

export const listPurchases = () => apiRequest("/purchases/");
export const getPurchase = (id) => apiRequest("/purchases/" + id + "/");
export const createPurchase = (data) => apiRequest("/purchases/", { method: "POST", body: JSON.stringify(data) });
export const updatePurchase = (id, data) => apiRequest("/purchases/" + id + "/", { method: "PATCH", body: JSON.stringify(data) });
export const addPurchaseItem = (purchaseId, data) => apiRequest("/purchases/" + purchaseId + "/items/", { method: "POST", body: JSON.stringify(data) });
export const updatePurchaseItem = (purchaseId, itemId, data) => apiRequest("/purchases/" + purchaseId + "/items/" + itemId + "/", { method: "PATCH", body: JSON.stringify(data) });
export const removePurchaseItem = (purchaseId, itemId) => apiRequest("/purchases/" + purchaseId + "/items/" + itemId + "/", { method: "DELETE" });
