import { apiRequest } from "./api";

const query = (from, to) => from && to ? `?from=${encodeURIComponent(from)}&to=${encodeURIComponent(to)}` : "";

export const getDashboard = (from, to) => apiRequest("/dashboard/" + query(from, to));
export const getSummaryReport = (from, to) => apiRequest("/reports/summary/" + query(from, to));
export const getProductReport = (from, to) => apiRequest("/reports/products/" + query(from, to));
export const getCustomerReport = (from, to) => apiRequest("/reports/customers/" + query(from, to));
