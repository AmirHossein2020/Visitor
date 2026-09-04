export function Icon({ name, className = "size-5" }) {
  const paths = {
    home: <><path d="M3 11 12 3l9 8"/><path d="M5 10v10h14V10M9 20v-6h6v6"/></>,
    users: <><circle cx="9" cy="8" r="3"/><path d="M3 20c0-4 2-7 6-7s6 3 6 7M16 5c3 0 4 5 1 6M17 14c2 0 4 2 4 5"/></>,
    orders: <><path d="M5 4h14v17H5zM8 8h8M8 12h8M8 16h5"/></>,
    invoice: <><path d="M6 3h10l3 3v15H6zM16 3v4h3M9 12h6M9 16h6"/></>,
    box: <><path d="m4 7 8-4 8 4-8 4zM4 7v10l8 4 8-4V7M12 11v10"/></>,
    chart: <><path d="M4 20V10M10 20V4M16 20v-7M22 20H2"/></>,
    more: <><circle cx="5" cy="12" r="1"/><circle cx="12" cy="12" r="1"/><circle cx="19" cy="12" r="1"/></>,
    back: <path d="m9 18 6-6-6-6"/>,
    plus: <path d="M12 5v14M5 12h14"/>,
    user: <><circle cx="12" cy="8" r="4"/><path d="M4 21c0-5 3-8 8-8s8 3 8 8"/></>,
    support: <><path d="M4 13v-2a8 8 0 0 1 16 0v2"/><path d="M4 13h3v6H5a1 1 0 0 1-1-1zM20 13h-3v6h2a1 1 0 0 0 1-1zM17 19c0 2-2 2-4 2"/></>,
  };
  return <svg aria-hidden="true" className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">{paths[name] || paths.box}</svg>;
}

export const Card = ({ className = "", children, ...props }) => <section className={`ui-card ${className}`} {...props}>{children}</section>;
export const Button = ({ variant = "primary", className = "", children, ...props }) => <button className={`ui-button ui-button-${variant} ${className}`} {...props}>{children}</button>;
export const Badge = ({ tone = "neutral", children }) => <span className={`ui-badge ui-badge-${tone}`}>{children}</span>;

export function StatePanel({ type = "loading", title, description, action }) {
  const defaults = {loading:["در حال دریافت اطلاعات…","کمی صبر کنید."],empty:["هنوز اطلاعاتی ثبت نشده است.","با اولین ثبت، اطلاعات این بخش اینجا نمایش داده می‌شود."],error:["دریافت اطلاعات ممکن نشد.","اتصال را بررسی کنید و دوباره تلاش کنید."]};
  return <div className={`ui-state ui-state-${type}`} role={type === "error" ? "alert" : "status"}><span className="ui-state-mark"/><div><h3>{title || defaults[type][0]}</h3><p>{description || defaults[type][1]}</p>{action}</div></div>;
}
