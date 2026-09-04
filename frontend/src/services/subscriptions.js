import { apiRequest } from "./api";
import { normalizePhone } from "./normalization";

export const listPlans = () => apiRequest("/subscriptions/plans/");
export const getMySubscription = () => apiRequest("/subscriptions/me/");
export const activateFreeTrial = () => apiRequest("/subscriptions/trial/activate/", { method: "POST" });
export const listSubscriptionOrders = () => apiRequest("/subscriptions/orders/");
export const createSubscriptionOrder = (planId) => apiRequest("/subscriptions/orders/", {
  method: "POST",
  body: JSON.stringify({ plan_id: planId }),
});
export const getPaymentInfo = () => apiRequest("/subscriptions/payment-info/");
export const listOrderPayments = (orderId) => apiRequest(`/subscriptions/orders/${orderId}/payments/`);
export const submitOrderPayment = (orderId, formData) => apiRequest(`/subscriptions/orders/${orderId}/payments/`, { method: "POST", body: formData });
export const getMyProfile = () => apiRequest("/auth/me/");
export const updateMyProfile = data => apiRequest("/auth/me/", { method: "PATCH", body: JSON.stringify({ ...data, phone_number: normalizePhone(data.phone_number) }) });
