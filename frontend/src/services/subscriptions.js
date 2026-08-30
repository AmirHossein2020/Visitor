import { apiRequest } from "./api";

export const listPlans = () => apiRequest("/subscriptions/plans/");
export const getMySubscription = () => apiRequest("/subscriptions/me/");
export const listSubscriptionOrders = () => apiRequest("/subscriptions/orders/");
export const createSubscriptionOrder = (planId) => apiRequest("/subscriptions/orders/", {
  method: "POST",
  body: JSON.stringify({ plan_id: planId }),
});
