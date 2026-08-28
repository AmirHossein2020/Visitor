import { apiRequest } from "./api";

export const listOrders = () => apiRequest("/orders/");
export const getOrder = (id) => apiRequest("/orders/" + id + "/");
export const createOrder = (data) =>
  apiRequest("/orders/", { method: "POST", body: JSON.stringify(data) });
export const updateOrder = (id, data) =>
  apiRequest("/orders/" + id + "/", { method: "PATCH", body: JSON.stringify(data) });
export const addOrderItem = (orderId, data) =>
  apiRequest("/orders/" + orderId + "/items/", { method: "POST", body: JSON.stringify(data) });
export const updateOrderItem = (orderId, itemId, data) =>
  apiRequest("/orders/" + orderId + "/items/" + itemId + "/", { method: "PATCH", body: JSON.stringify(data) });
export const removeOrderItem = (orderId, itemId) =>
  apiRequest("/orders/" + orderId + "/items/" + itemId + "/", { method: "DELETE" });
