import { lazy, Suspense, useEffect, useState } from "react";
import { navigate, useRoute } from "./hooks/useRoute";
import { useAuth } from "./services/AuthContext";
import { getMySubscription } from "./services/subscriptions";
import { AdminErrorBoundary, AdminUnavailable } from "./components/platform-admin/AdminUI";

const pages = {
  Landing: lazy(() => import("./pages/LandingPage")), Login: lazy(() => import("./pages/LoginPage")), Register: lazy(() => import("./pages/RegisterPage")),
  AdminDashboard: lazy(() => import("./pages/platform-admin/AdminDashboardPage")), AdminUsers: lazy(() => import("./pages/platform-admin/AdminUsersPage")), AdminUserDetail: lazy(() => import("./pages/platform-admin/AdminUserDetailPage")),
  AdminOrders: lazy(() => import("./pages/platform-admin/AdminSubscriptionOrdersPage")), AdminPayments: lazy(() => import("./pages/platform-admin/AdminPaymentsPage")), AdminSubscriptions: lazy(() => import("./pages/platform-admin/AdminSubscriptionsPage")), AdminPlans: lazy(() => import("./pages/platform-admin/AdminPlansPage")),
  AdminSettings: lazy(() => import("./pages/platform-admin/AdminSettingsPage")), AdminAuditLog: lazy(() => import("./pages/platform-admin/AdminAuditLogPage")),
  SubscriptionPayment: lazy(() => import("./pages/SubscriptionPaymentPage")),
  Pricing: lazy(() => import("./pages/PricingPage")), Profile: lazy(() => import("./pages/ProfilePage")), Subscription: lazy(() => import("./pages/SubscriptionPage")), Required: lazy(() => import("./pages/SubscriptionRequiredPage")), Home: lazy(() => import("./pages/HomePage")),
  Customers: lazy(() => import("./pages/CustomerListPage")), CustomerNew: lazy(() => import("./pages/CustomerCreatePage")), CustomerDetail: lazy(() => import("./pages/CustomerDetailPage")), CustomerEdit: lazy(() => import("./pages/CustomerEditPage")),
  Products: lazy(() => import("./pages/ProductListPage")), ProductNew: lazy(() => import("./pages/ProductCreatePage")), ProductEdit: lazy(() => import("./pages/ProductEditPage")),
  Orders: lazy(() => import("./pages/OrderListPage")), OrderNew: lazy(() => import("./pages/OrderCreatePage")), OrderDetail: lazy(() => import("./pages/OrderDetailPage")),
  Purchases: lazy(() => import("./pages/PurchaseListPage")), PurchaseNew: lazy(() => import("./pages/PurchaseCreatePage")), PurchaseDetail: lazy(() => import("./pages/PurchaseDetailPage")),
  Invoices: lazy(() => import("./pages/InvoiceListPage")), InvoiceNew: lazy(() => import("./pages/InvoiceCreatePage")), InvoiceDetail: lazy(() => import("./pages/InvoiceDetailPage")),
  Returns: lazy(() => import("./pages/ReturnListPage")), ReturnNew: lazy(() => import("./pages/ReturnCreatePage")), ReturnDetail: lazy(() => import("./pages/ReturnDetailPage")),
  Inventory: lazy(() => import("./pages/InventoryListPage")), InventoryDetail: lazy(() => import("./pages/InventoryDetailPage")), Reports: lazy(() => import("./pages/ReportsPage")),
  Companies: lazy(() => import("./pages/CompanyListPage")), CompanyNew: lazy(() => import("./pages/CompanyCreatePage")), CompanyDetail: lazy(() => import("./pages/CompanyDetailPage")), CompanyEdit: lazy(() => import("./pages/CompanyEditPage")),
};

function BusinessGate({ children }) {
  const [state, setState] = useState(null);
  useEffect(() => { getMySubscription().then(setState).catch(() => setState({ is_active: false })); }, []);
  if (!state) return <main className="grid min-h-dvh place-items-center bg-slate-50">در حال بررسی اشتراک…</main>;
  return state.is_active ? children : <pages.Required />;
}

function businessPage(path) {
  if (path === "/app") return <pages.Home />;
  if (path === "/invoices") return <pages.Invoices />;
  if (path === "/reports") return <pages.Reports />;
  if (path === "/inventory") return <pages.Inventory />;
  if (path === "/returns") return <pages.Returns />;
  if (path === "/companies") return <pages.Companies />;
  if (path === "/companies/new") return <pages.CompanyNew />;
  if (path === "/purchases") return <pages.Purchases />;
  if (path === "/orders") return <pages.Orders />;
  if (path === "/customers") return <pages.Customers />;
  if (path === "/customers/new") return <pages.CustomerNew />;
  if (path === "/products") return <pages.Products />;
  if (path === "/products/new") return <pages.ProductNew />;
  let match = path.match(/^\/inventory\/(\d+)$/); if (match) return <pages.InventoryDetail productId={match[1]} />;
  match = path.match(/^\/invoices\/(\d+)\/returns\/new$/); if (match) return <pages.ReturnNew invoiceId={match[1]} />;
  match = path.match(/^\/returns\/(\d+)$/); if (match) return <pages.ReturnDetail returnId={match[1]} />;
  match = path.match(/^\/orders\/(\d+)\/invoice\/new$/); if (match) return <pages.InvoiceNew orderId={match[1]} />;
  match = path.match(/^\/invoices\/(\d+)$/); if (match) return <pages.InvoiceDetail invoiceId={match[1]} />;
  match = path.match(/^\/companies\/(\d+)\/edit$/); if (match) return <pages.CompanyEdit companyId={match[1]} />;
  match = path.match(/^\/companies\/(\d+)$/); if (match) return <pages.CompanyDetail companyId={match[1]} />;
  match = path.match(/^\/customers\/(\d+)\/purchases\/new$/); if (match) return <pages.PurchaseNew customerId={match[1]} />;
  match = path.match(/^\/purchases\/(\d+)$/); if (match) return <pages.PurchaseDetail purchaseId={match[1]} />;
  match = path.match(/^\/customers\/(\d+)\/orders\/new$/); if (match) return <pages.OrderNew customerId={match[1]} />;
  match = path.match(/^\/orders\/(\d+)$/); if (match) return <pages.OrderDetail orderId={match[1]} />;
  match = path.match(/^\/customers\/(\d+)\/edit$/); if (match) return <pages.CustomerEdit customerId={match[1]} />;
  match = path.match(/^\/customers\/(\d+)$/); if (match) return <pages.CustomerDetail customerId={match[1]} />;
  match = path.match(/^\/products\/(\d+)\/edit$/); if (match) return <pages.ProductEdit productId={match[1]} />;
  return null;
}

function AppRoutes() {
  const path = useRoute(); const { user, isLoading, authError, loadUser } = useAuth();
  const isPlatformAdmin = Boolean(user?.is_staff || user?.is_superuser);
  useEffect(() => { if (!isLoading && !user && path.startsWith("/account")) navigate("/login", { replace: true }); }, [user,isLoading,path]);
  if (isLoading) return <main className="grid min-h-dvh place-items-center bg-slate-50">در حال بررسی حساب…</main>;
  if (path.startsWith("/platform-admin") && authError?.status === 0) return <AdminErrorBoundary><AdminUnavailable retry={loadUser}/></AdminErrorBoundary>;
  if (path === "/") return <pages.Landing />;
  if (path === "/pricing") return <pages.Pricing />;
  if (path === "/register" && !user) return <pages.Register />;
  if (path === "/login" && !user) return <pages.Login />;
  if (["/login","/register","/account/subscription","/account/profile"].includes(path) && isPlatformAdmin) { navigate("/platform-admin", { replace: true }); return null; }
  if (path === "/account/profile" && user) return <pages.Profile />;
  if (path === "/account/subscription" && user) return <pages.Subscription />;
  const paymentMatch = path.match(/^\/account\/subscription\/orders\/(\d+)\/payment$/);
  if (paymentMatch && user) return <pages.SubscriptionPayment orderId={paymentMatch[1]} />;
  if (path.startsWith("/platform-admin")) {
    if (!user) { navigate("/login", { replace: true }); return null; }
    if (!isPlatformAdmin) { navigate("/account/subscription", { replace: true }); return null; }
    const safeAdmin = page => <AdminErrorBoundary key={path}>{page}</AdminErrorBoundary>;
    if (path === "/platform-admin") return safeAdmin(<pages.AdminDashboard />);
    if (path === "/platform-admin/users") return safeAdmin(<pages.AdminUsers />);
    let adminDetail = path.match(/^\/platform-admin\/users\/(\d+)$/); if (adminDetail) return safeAdmin(<pages.AdminUserDetail userId={adminDetail[1]} />);
    if (path === "/platform-admin/subscription-orders") return safeAdmin(<pages.AdminOrders />);
    adminDetail = path.match(/^\/platform-admin\/subscription-orders\/(\d+)$/); if (adminDetail) return safeAdmin(<pages.AdminOrders orderId={adminDetail[1]} />);
    if (path === "/platform-admin/payments") return safeAdmin(<pages.AdminPayments />);
    adminDetail = path.match(/^\/platform-admin\/payments\/(\d+)$/); if (adminDetail) return safeAdmin(<pages.AdminPayments paymentId={adminDetail[1]} />);
    if (path === "/platform-admin/subscriptions") return safeAdmin(<pages.AdminSubscriptions />);
    if (path === "/platform-admin/plans") return safeAdmin(<pages.AdminPlans />);
    if (path === "/platform-admin/settings") return safeAdmin(<pages.AdminSettings />);
    if (path === "/platform-admin/audit-log") return safeAdmin(<pages.AdminAuditLog />);
  }
  const business = businessPage(path);
  if (business) {
    if (!user) { navigate("/login", { replace: true }); return null; }
    return <BusinessGate>{business}</BusinessGate>;
  }
  if (user) return <pages.Subscription />;
  return <pages.Landing />;
}

export default function App(){return <Suspense fallback={<main className="grid min-h-dvh place-items-center bg-slate-50">در حال بارگذاری…</main>}><AppRoutes /></Suspense>}
