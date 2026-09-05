import { useState } from "react";
import { navigate } from "../hooks/useRoute";
import { useAuth } from "../services/AuthContext";
import MobileNav from "./MobileNav";
import { Icon } from "./ui";

export const businessLinks = [
  ["اصلی", [["داشبورد","/app","home"]]],
  ["فروش", [["مشتریان","/customers","users"],["سفارش‌ها","/orders","orders"],["فاکتورها","/invoices","invoice"],["مرجوعی‌ها","/returns","back"]]],
  ["کالا و عملیات", [["کالاها","/products","box"],["خریدها","/purchases","orders"],["موجودی","/inventory","box"]]],
  ["مدیریت", [["گزارش‌ها","/reports","chart"],["کسب‌وکار","/companies","box"],["پشتیبانی","/support","support"],["پروفایل","/account/profile","user"],["اشتراک","/account/subscription","invoice"]]],
];

const activeFor = href => location.pathname === href || location.pathname.startsWith(`${href}/`);

export default function AppShell({ title, subtitle, backPath, action, children }) {
  const { user, logout } = useAuth();
  const [moreOpen, setMoreOpen] = useState(false);
  return <div className="app-shell"><aside className="app-sidebar"><button className="brand-lockup" onClick={()=>navigate("/app")}><span className="brand-mark">و</span><span><b>ویزیتورکار</b><small>مدیریت فروش</small></span></button><nav aria-label="ناوبری کسب‌وکار">{businessLinks.map(([group,links])=><div className="sidebar-group" key={group}><p>{group}</p>{links.map(([label,href,icon])=><button aria-current={activeFor(href)?"page":undefined} className={activeFor(href)?"active":""} key={href} onClick={()=>navigate(href)}><Icon name={icon}/><span>{label}</span></button>)}</div>)}</nav><div className="sidebar-account"><span className="avatar">{user?.full_name?.trim()?.[0] || "ک"}</span><div><b>{user?.full_name || "کاربر"}</b><button onClick={()=>{logout();navigate("/login")}}>خروج از حساب</button></div></div></aside><div className="app-workspace"><header className="app-topbar"><div className="page-context">{backPath&&<button aria-label="بازگشت" className="back-button" onClick={()=>navigate(backPath)}><Icon name="back"/></button>}<div><p>پنل کسب‌وکار</p><h1>{title}</h1>{subtitle&&<span>{subtitle}</span>}</div></div>{action&&<div className="page-action">{action}</div>}<button className="mobile-account" aria-label="حساب کاربری" onClick={()=>navigate("/account/profile")}><Icon name="user"/></button></header><main className="app-content">{children}</main></div><MobileNav moreOpen={moreOpen} setMoreOpen={setMoreOpen}/></div>;
}
