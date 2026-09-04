import OrderLayout from "./OrderLayout";

export default function ProductLayout({ title, children, showBack = false }) {
  return <OrderLayout title={title} backPath={showBack ? "/products" : "/app"}>{children}</OrderLayout>;
}
