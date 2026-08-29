import { apiRequest } from "./api";

export const listReturns = () => apiRequest("/returns/");
export const getReturn = (id) => apiRequest("/returns/" + id + "/");
export const createReturn = (data) => apiRequest("/returns/", { method: "POST", body: JSON.stringify(data) });
export const updateReturn = (id, data) => apiRequest("/returns/" + id + "/", { method: "PATCH", body: JSON.stringify(data) });
export const cancelReturn = (id) => apiRequest("/returns/" + id + "/", { method: "DELETE" });
export const addReturnItem = (returnId, data) => apiRequest("/returns/" + returnId + "/items/", { method: "POST", body: JSON.stringify(data) });
export const updateReturnItem = (returnId, itemId, data) => apiRequest("/returns/" + returnId + "/items/" + itemId + "/", { method: "PATCH", body: JSON.stringify(data) });
export const removeReturnItem = (returnId, itemId) => apiRequest("/returns/" + returnId + "/items/" + itemId + "/", { method: "DELETE" });
