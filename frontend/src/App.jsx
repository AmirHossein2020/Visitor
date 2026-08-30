import { lazy, Suspense, useEffect, useState } from "react";
import { navigate, useRoute } from "./hooks/useRoute";
import { useAuth } from "./services/AuthContext";
import { getMySubscription } from "./services/subscriptions";

const pages = {
  Landing: lazy(() => import("./pages/LandingPage")), Login: lazy(() => import("./pages/LoginPage")), Register: lazy(() => import("./pages/RegisterPage")),
  Pricing: lazy(() => import("./pages/PricingPage")), Subscription: lazy(() => import("./pages/SubscriptionPage")), Required: lazy(() => import("./pages/SubscriptionRequiredPage")), Home: lazy(() => import("./pages/HomePage")),
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
  const path = useRoute(); const { user, isLoading } = useAuth();
  useEffect(() => { if (!isLoading && !user && path.startsWith("/account")) navigate("/login", { replace: true }); }, [user,isLoading,path]);
  if (isLoading) return <main className="grid min-h-dvh place-items-center bg-slate-50">در حال بررسی حساب…</main>;
  if (path === "/") return <pages.Landing />;
  if (path === "/pricing") return <pages.Pricing />;
  if (path === "/register" && !user) return <pages.Register />;
  if (path === "/login" && !user) return <pages.Login />;
  if (path === "/account/subscription" && user) return <pages.Subscription />;
  const business = businessPage(path);
  if (business) {
    if (!user) { navigate("/login", { replace: true }); return null; }
    return <BusinessGate>{business}</BusinessGate>;
  }
  if (user) return <pages.Subscription />;
  return <pages.Landing />;
}

export default function App(){return <Suspense fallback={<main className="grid min-h-dvh place-items-center bg-slate-50">در حال بارگذاری…</main>}><AppRoutes /></Suspense>}
