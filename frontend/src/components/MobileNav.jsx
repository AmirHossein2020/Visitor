import { navigate } from "../hooks/useRoute";
import { Icon } from "./ui";

const primary = [["داشبورد","/app","home"],["مشتریان","/customers","users"],["سفارش‌ها","/orders","orders"],["فاکتورها","/invoices","invoice"]];
const secondary = [["کالاها","/products","box"],["خریدها","/purchases","orders"],["موجودی","/inventory","box"],["مرجوعی‌ها","/returns","back"],["گزارش‌ها","/reports","chart"],["کسب‌وکار","/companies","box"],["پشتیبانی","/support","support"],["پروفایل","/account/profile","user"],["اشتراک","/account/subscription","invoice"]];
const activeFor = href => location.pathname === href || location.pathname.startsWith(`${href}/`);

export default function MobileNav({ moreOpen = false, setMoreOpen = () => {} }) {
  return <>{moreOpen&&<div className="mobile-more-backdrop" onClick={()=>setMoreOpen(false)}><section aria-label="بخش‌های بیشتر" className="mobile-more" onClick={event=>event.stopPropagation()}><header><div><p>دسترسی سریع</p><h2>بخش‌های بیشتر</h2></div><button aria-label="بستن" onClick={()=>setMoreOpen(false)}>×</button></header><div>{secondary.map(([label,href,icon])=><button key={href} onClick={()=>{setMoreOpen(false);navigate(href)}}><Icon name={icon}/><span>{label}</span></button>)}</div></section></div>}<nav className="mobile-bottom-nav" aria-label="ناوبری اصلی موبایل">{primary.map(([label,href,icon])=><button aria-current={activeFor(href)?"page":undefined} className={activeFor(href)?"active":""} key={href} onClick={()=>navigate(href)}><Icon name={icon}/><span>{label}</span></button>)}<button className={moreOpen?"active":""} onClick={()=>setMoreOpen(!moreOpen)}><Icon name="more"/><span>بیشتر</span></button></nav></>;
}
