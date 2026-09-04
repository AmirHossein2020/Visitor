import { apiBlob, apiRequest } from "./api.js";

const query = (params = {}) => { const value = new URLSearchParams(Object.entries(params).filter(([, item]) => item !== "" && item != null)).toString(); return value ? `?${value}` : ""; };
const unwrap = (response) => response?.data ?? response;
const collection = (value) => Array.isArray(value) ? value : Array.isArray(value?.results) ? value.results : [];

export const supportLabels = {
  statuses: { open: "باز", in_progress: "در حال بررسی", waiting_for_customer: "در انتظار پاسخ شما", resolved: "حل شده", closed: "بسته شده" },
  categories: { technical: "مشکل فنی", usage: "سوال درباره استفاده از سامانه", order_invoice: "سفارش و فاکتور", data: "اطلاعات و داده‌ها", subscription: "اشتراک و پرداخت", account: "حساب کاربری", feedback: "پیشنهاد و بازخورد", other: "سایر" },
  priorities: { low: "کم", normal: "عادی", high: "مهم" },
};

export function normalizeAttachment(value = {}) { return { id: value?.id ?? null, original_name: value?.original_name || "پیوست", content_type: value?.content_type || "application/octet-stream", size: Number(value?.size) || 0, download_url: value?.download_url || "", created_at: value?.created_at || null }; }
export function normalizeMessage(value = {}) { return { id: value?.id ?? null, sender_name: value?.sender_name || "کاربر", sender_role: value?.sender_role || (value?.is_staff_reply ? "support" : "customer"), body: typeof value?.body === "string" ? value.body : "", is_staff_reply: Boolean(value?.is_staff_reply), is_internal_note: Boolean(value?.is_internal_note), attachments: collection(value?.attachments).map(normalizeAttachment), created_at: value?.created_at || null }; }
export function normalizeTicket(response) {
  const value = unwrap(response) || {};
  return { ...value, id: value.id ?? null, ticket_number: value.ticket_number || "—", subject: value.subject || "درخواست پشتیبانی", category: value.category || "other", priority: value.priority || "normal", status: value.status || "open", category_display: value.category_display || supportLabels.categories[value.category] || value.category || "—", priority_display: value.priority_display || supportLabels.priorities[value.priority] || value.priority || "—", status_display: value.status_display || supportLabels.statuses[value.status] || value.status || "—", messages: collection(value.messages).map(normalizeMessage), subscription_summary: value.subscription_summary || null, assigned_admin: value.assigned_admin ?? null, assigned_admin_email: value.assigned_admin_email || null, context_label: value.context_label || "", created_at: value.created_at || null, updated_at: value.updated_at || null, last_message_at: value.last_message_at || null };
}
export function normalizeTicketList(response) { const value = unwrap(response); const results = collection(value).map(normalizeTicket); return Array.isArray(value) ? { count: results.length, next: null, previous: null, results } : { count: Number(value?.count) || results.length, next: value?.next || null, previous: value?.previous || null, results }; }

export const listTickets = (params) => apiRequest(`/support/tickets/${query(params)}`).then(normalizeTicketList);
export const getTicket = (id) => apiRequest(`/support/tickets/${id}/`).then(normalizeTicket);
export const createTicket = (data) => apiRequest("/support/tickets/", { method: "POST", body: data }).then(normalizeTicket);
export const replyTicket = (id, data) => apiRequest(`/support/tickets/${id}/messages/`, { method: "POST", body: data }).then(normalizeTicket);
export const closeTicket = (id) => apiRequest(`/support/tickets/${id}/close/`, { method: "POST", body: "{}" }).then(normalizeTicket);
export const downloadSupportAttachment = (id) => apiBlob(`/support/attachments/${id}/download/`);
export const adminListTickets = (params) => apiRequest(`/platform-admin/support/tickets/${query(params)}`).then(normalizeTicketList);
export const adminGetTicket = (id) => apiRequest(`/platform-admin/support/tickets/${id}/`).then(normalizeTicket);
export const adminReplyTicket = (id, data) => apiRequest(`/platform-admin/support/tickets/${id}/reply/`, { method: "POST", body: data }).then(normalizeTicket);
export const adminTicketStatus = (id, status) => apiRequest(`/platform-admin/support/tickets/${id}/status/`, { method: "POST", body: JSON.stringify({ status }) }).then(normalizeTicket);
export const adminAssignTicket = (id, assigned_admin_id) => apiRequest(`/platform-admin/support/tickets/${id}/assign/`, { method: "POST", body: JSON.stringify({ assigned_admin_id }) }).then(normalizeTicket);
export const adminInternalNote = (id, body) => apiRequest(`/platform-admin/support/tickets/${id}/internal-note/`, { method: "POST", body: JSON.stringify({ body }) }).then(normalizeTicket);
