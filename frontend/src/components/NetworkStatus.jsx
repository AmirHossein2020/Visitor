import { useEffect, useState } from "react";

export default function NetworkStatus() {
  const [online, setOnline] = useState(navigator.onLine);
  useEffect(() => {
    const update = () => setOnline(navigator.onLine);
    window.addEventListener("online", update);
    window.addEventListener("offline", update);
    return () => { window.removeEventListener("online", update); window.removeEventListener("offline", update); };
  }, []);
  if (online) return null;
  return <div className="fixed inset-x-3 top-3 z-[60] mx-auto max-w-md rounded-xl bg-amber-100 px-4 py-3 text-center text-sm font-semibold text-amber-900 shadow-lg ring-1 ring-amber-300" role="status">اینترنت قطع است؛ عملیات نیازمند سرور انجام نمی‌شود.</div>;
}
