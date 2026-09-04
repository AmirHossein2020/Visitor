import AppShell from "../components/AppShell";

export default function OrderLayout({ title, subtitle, children, backPath = "/orders", action }) {
  return <AppShell title={title} subtitle={subtitle} backPath={backPath} action={action}>{children}</AppShell>;
}
