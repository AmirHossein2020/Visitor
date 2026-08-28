import { useEffect } from "react";
import { navigate, useRoute } from "./hooks/useRoute";
import HomePage from "./pages/HomePage";
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
