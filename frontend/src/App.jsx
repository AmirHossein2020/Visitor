import { useEffect } from "react";
import { navigate, useRoute } from "./hooks/useRoute";
import HomePage from "./pages/HomePage";
import InvoiceCreatePage from "./pages/InvoiceCreatePage";
import InvoiceDetailPage from "./pages/InvoiceDetailPage";
import InvoiceListPage from "./pages/InvoiceListPage";
import CompanyCreatePage from "./pages/CompanyCreatePage";
import CompanyDetailPage from "./pages/CompanyDetailPage";
import CompanyEditPage from "./pages/CompanyEditPage";
import CompanyListPage from "./pages/CompanyListPage";
import CustomerCreatePage from "./pages/CustomerCreatePage";
import CustomerDetailPage from "./pages/CustomerDetailPage";
import CustomerEditPage from "./pages/CustomerEditPage";
import CustomerListPage from "./pages/CustomerListPage";
import LoginPage from "./pages/LoginPage";
import OrderCreatePage from "./pages/OrderCreatePage";
import OrderDetailPage from "./pages/OrderDetailPage";
import OrderListPage from "./pages/OrderListPage";
import ProductCreatePage from "./pages/ProductCreatePage";
import ProductEditPage from "./pages/ProductEditPage";
import ProductListPage from "./pages/ProductListPage";
import PurchaseCreatePage from "./pages/PurchaseCreatePage";
import PurchaseDetailPage from "./pages/PurchaseDetailPage";
import PurchaseListPage from "./pages/PurchaseListPage";
import RegisterPage from "./pages/RegisterPage";
import { useAuth } from "./services/AuthContext";

function App() {
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

export default App;
