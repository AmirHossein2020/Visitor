import { lazy, Suspense, useEffect } from "react";
import { navigate, useRoute } from "./hooks/useRoute";
import { useAuth } from "./services/AuthContext";

const HomePage = lazy(() => import("./pages/HomePage"));
const LoginPage = lazy(() => import("./pages/LoginPage"));
const RegisterPage = lazy(() => import("./pages/RegisterPage"));
const CustomerListPage = lazy(() => import("./pages/CustomerListPage"));
const CustomerCreatePage = lazy(() => import("./pages/CustomerCreatePage"));
const CustomerDetailPage = lazy(() => import("./pages/CustomerDetailPage"));
const CustomerEditPage = lazy(() => import("./pages/CustomerEditPage"));
const ProductListPage = lazy(() => import("./pages/ProductListPage"));
const ProductCreatePage = lazy(() => import("./pages/ProductCreatePage"));
const ProductEditPage = lazy(() => import("./pages/ProductEditPage"));
const OrderListPage = lazy(() => import("./pages/OrderListPage"));
const OrderCreatePage = lazy(() => import("./pages/OrderCreatePage"));
const OrderDetailPage = lazy(() => import("./pages/OrderDetailPage"));
const PurchaseListPage = lazy(() => import("./pages/PurchaseListPage"));
const PurchaseCreatePage = lazy(() => import("./pages/PurchaseCreatePage"));
const PurchaseDetailPage = lazy(() => import("./pages/PurchaseDetailPage"));
const InvoiceListPage = lazy(() => import("./pages/InvoiceListPage"));
const InvoiceCreatePage = lazy(() => import("./pages/InvoiceCreatePage"));
const InvoiceDetailPage = lazy(() => import("./pages/InvoiceDetailPage"));
const ReturnListPage = lazy(() => import("./pages/ReturnListPage"));
const ReturnCreatePage = lazy(() => import("./pages/ReturnCreatePage"));
const ReturnDetailPage = lazy(() => import("./pages/ReturnDetailPage"));
const InventoryListPage = lazy(() => import("./pages/InventoryListPage"));
const InventoryDetailPage = lazy(() => import("./pages/InventoryDetailPage"));
const CompanyListPage = lazy(() => import("./pages/CompanyListPage"));
const CompanyCreatePage = lazy(() => import("./pages/CompanyCreatePage"));
const CompanyDetailPage = lazy(() => import("./pages/CompanyDetailPage"));
const CompanyEditPage = lazy(() => import("./pages/CompanyEditPage"));
const ReportsPage = lazy(() => import("./pages/ReportsPage"));

function AppRoutes() {
  const path = useRoute();
  const { user, isLoading } = useAuth();

  useEffect(() => {
    if (isLoading) return;
    if (!user && path !== "/login" && path !== "/register") navigate("/login", { replace: true });
    if (user && (path === "/login" || path === "/register")) navigate("/", { replace: true });
  }, [user, isLoading, path]);

  if (isLoading) return <main className="flex min-h-dvh items-center justify-center bg-slate-50 text-slate-600">در حال بررسی حساب…</main>;
  if (path === "/register" && !user) return <RegisterPage />;
  if (path === "/login" && !user) return <LoginPage />;
  if (user && path === "/invoices") return <InvoiceListPage />;
  if (user && path === "/reports") return <ReportsPage />;
  if (user && path === "/inventory") return <InventoryListPage />;
  const inventoryDetailMatch = path.match(/^\/inventory\/(\d+)$/);
  if (user && inventoryDetailMatch) return <InventoryDetailPage productId={inventoryDetailMatch[1]} />;
  if (user && path === "/returns") return <ReturnListPage />;
  const returnCreateMatch = path.match(/^\/invoices\/(\d+)\/returns\/new$/);
  if (user && returnCreateMatch) return <ReturnCreatePage invoiceId={returnCreateMatch[1]} />;
  const returnDetailMatch = path.match(/^\/returns\/(\d+)$/);
  if (user && returnDetailMatch) return <ReturnDetailPage returnId={returnDetailMatch[1]} />;
  const invoiceCreateMatch = path.match(/^\/orders\/(\d+)\/invoice\/new$/);
  if (user && invoiceCreateMatch) return <InvoiceCreatePage orderId={invoiceCreateMatch[1]} />;
  const invoiceDetailMatch = path.match(/^\/invoices\/(\d+)$/);
  if (user && invoiceDetailMatch) return <InvoiceDetailPage invoiceId={invoiceDetailMatch[1]} />;
  if (user && path === "/companies") return <CompanyListPage />;
  if (user && path === "/companies/new") return <CompanyCreatePage />;
  const companyEditMatch = path.match(/^\/companies\/(\d+)\/edit$/);
  if (user && companyEditMatch) return <CompanyEditPage companyId={companyEditMatch[1]} />;
  const companyDetailMatch = path.match(/^\/companies\/(\d+)$/);
  if (user && companyDetailMatch) return <CompanyDetailPage companyId={companyDetailMatch[1]} />;
  if (user && path === "/purchases") return <PurchaseListPage />;
  const purchaseCreateMatch = path.match(/^\/customers\/(\d+)\/purchases\/new$/);
  if (user && purchaseCreateMatch) return <PurchaseCreatePage customerId={purchaseCreateMatch[1]} />;
  const purchaseDetailMatch = path.match(/^\/purchases\/(\d+)$/);
  if (user && purchaseDetailMatch) return <PurchaseDetailPage purchaseId={purchaseDetailMatch[1]} />;
  if (user && path === "/orders") return <OrderListPage />;
  const orderCreateMatch = path.match(/^\/customers\/(\d+)\/orders\/new$/);
  if (user && orderCreateMatch) return <OrderCreatePage customerId={orderCreateMatch[1]} />;
  const orderDetailMatch = path.match(/^\/orders\/(\d+)$/);
  if (user && orderDetailMatch) return <OrderDetailPage orderId={orderDetailMatch[1]} />;
  if (user && path === "/customers") return <CustomerListPage />;
  if (user && path === "/customers/new") return <CustomerCreatePage />;
  const customerEditMatch = path.match(/^\/customers\/(\d+)\/edit$/);
  if (user && customerEditMatch) return <CustomerEditPage customerId={customerEditMatch[1]} />;
  const customerDetailMatch = path.match(/^\/customers\/(\d+)$/);
  if (user && customerDetailMatch) return <CustomerDetailPage customerId={customerDetailMatch[1]} />;
  if (user && path === "/products") return <ProductListPage />;
  if (user && path === "/products/new") return <ProductCreatePage />;
  const editMatch = path.match(/^\/products\/(\d+)\/edit$/);
  if (user && editMatch) return <ProductEditPage productId={editMatch[1]} />;
  if (user) return <HomePage />;
  return null;
}

function App() {
  return <Suspense fallback={<main className="flex min-h-dvh items-center justify-center bg-slate-50 text-slate-600">در حال بارگذاری…</main>}><AppRoutes /></Suspense>;
}

export default App;
