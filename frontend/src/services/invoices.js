import { apiBlob, apiRequest } from "./api";

export const listInvoices = () => apiRequest("/invoices/");
export const getInvoice = (id) => apiRequest("/invoices/" + id + "/");
export const issueInvoice = (data) => apiRequest("/invoices/", { method: "POST", body: JSON.stringify(data) });
export const cancelInvoice = (id) => apiRequest("/invoices/" + id + "/", { method: "DELETE" });
export const downloadInvoicePdf = (id) => apiBlob("/invoices/" + id + "/pdf/");
