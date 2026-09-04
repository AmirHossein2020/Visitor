import OrderLayout from "./OrderLayout";

export default function CustomerLayout({ title, children, showBack = false }) {
  return <OrderLayout title={title} backPath={showBack ? "/customers" : "/app"}>{children}</OrderLayout>;
}
