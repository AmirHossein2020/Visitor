import { useEffect, useState } from "react";
import { AdminLayout, StateBox } from "../../components/platform-admin/AdminUI";
import { formatJalaliDateTime } from "../../services/jalali";
import { navigate } from "../../hooks/useRoute";
import { getAdminErrorMessage } from "../../services/api";
import { adminAssignTicket, adminGetTicket, adminInternalNote, adminReplyTicket, adminTicketStatus, downloadSupportAttachment, supportLabels } from "../../services/support";

export default function AdminSupportDetailPage({ ticketId }) {
  const [ticket, setTicket] = useState();
  const [reply, setReply] = useState("");
  const [files, setFiles] = useState([]);
  const [note, setNote] = useState("");
  const [error, setError] = useState("");
  const load = () => { setError(""); return adminGetTicket(ticketId).then(setTicket).catch((requestError) => { setTicket(null); setError(requestError?.status === 404 ? "این تیکت پشتیبانی پیدا نشد." : getAdminErrorMessage(requestError)); }); };
  useEffect(() => {
    let active = true;
    setError("");
    adminGetTicket(ticketId)
      .then((result) => { if (active) setTicket(result); })
      .catch((requestError) => { if (active) { setTicket(null); setError(requestError?.status === 404 ? "این تیکت پشتیبانی پیدا نشد." : getAdminErrorMessage(requestError)); } });
    return () => { active = false; };
  }, [ticketId]);
  const safely = async (operation) => { setError(""); try { setTicket(await operation()); return true; } catch (requestError) { setError(getAdminErrorMessage(requestError)); return false; } };
  const send = async (event) => { event.preventDefault(); const data = new FormData(); data.append("body", reply); files.forEach((file) => data.append("attachments", file)); if (await safely(() => adminReplyTicket(ticketId, data))) { setReply(""); setFiles([]); } };
  if (!ticket) return <AdminLayout title="جزئیات پشتیبانی"><StateBox loading={!error} error={error && `خطا در دریافت تیکت پشتیبانی: ${error}`} retry={load} />{error && <button className="admin-button mt-3" onClick={() => navigate("/platform-admin/support")}>بازگشت به فهرست پشتیبانی</button>}</AdminLayout>;
  return <AdminLayout title={`${ticket.ticket_number} · ${ticket.subject}`} subtitle={`${ticket.user_name || ticket.user_email} — ${ticket.user_email}`}>
    <div className="admin-support-detail">
      <aside>
        <section><h3>اطلاعات درخواست</h3><dl>
          <div><dt>وضعیت</dt><dd>{supportLabels.statuses[ticket.status]}</dd></div><div><dt>دسته</dt><dd>{supportLabels.categories[ticket.category]}</dd></div><div><dt>اولویت</dt><dd>{supportLabels.priorities[ticket.priority]}</dd></div><div><dt>حساب</dt><dd>{ticket.user_is_active ? "فعال" : "غیرفعال"}</dd></div><div><dt>اشتراک</dt><dd>{ticket.subscription_summary?.plan || "بدون اشتراک"}</dd></div><div><dt>مسئول</dt><dd>{ticket.assigned_admin_email || "تخصیص نیافته"}</dd></div>
        </dl><select className="admin-input w-full" value={ticket.status} onChange={async (event) => setTicket(await adminTicketStatus(ticket.id, event.target.value))}>{Object.entries(supportLabels.statuses).map(([value, label]) => <option key={value} value={value}>{label}</option>)}</select><button className="admin-button mt-2 w-full bg-slate-950 text-white" onClick={async () => setTicket(await adminAssignTicket(ticket.id, "self"))}>تخصیص به من</button>{ticket.assigned_admin && <button className="admin-button mt-2 w-full" onClick={async () => setTicket(await adminAssignTicket(ticket.id, null))}>لغو تخصیص</button>}</section>
        <section><h3>یادداشت داخلی</h3><textarea className="admin-input min-h-24 w-full" value={note} onChange={(event) => setNote(event.target.value)} /><button className="admin-button mt-2 w-full" disabled={!note.trim()} onClick={async () => { setTicket(await adminInternalNote(ticket.id, note)); setNote(""); }}>ثبت یادداشت خصوصی</button></section>
      </aside>
      <main><div className="admin-message-list">{ticket.messages.map((message) => <article key={message.id} className={message.is_internal_note ? "internal" : message.is_staff_reply ? "staff" : "customer"}><header><strong>{message.is_internal_note ? "یادداشت داخلی" : message.sender_name}</strong><time>{formatJalaliDateTime(message.created_at)}</time></header><p>{message.body}</p>{message.attachments.map((item) => <button key={item.id} onClick={async () => window.open(URL.createObjectURL(await downloadSupportAttachment(item.id)), "_blank", "noopener")}>پیوست: {item.original_name}</button>)}</article>)}</div><form className="admin-reply" onSubmit={send}><label>پاسخ به کاربر<textarea required className="admin-input min-h-28 w-full" value={reply} onChange={(event) => setReply(event.target.value)} /></label><label>پیوست اختیاری<input type="file" multiple accept="image/jpeg,image/png,image/webp,application/pdf" onChange={(event) => setFiles([...event.target.files])} /></label><button className="admin-button bg-emerald-700 text-white">ارسال پاسخ و انتظار برای کاربر</button></form></main>
    </div>
  </AdminLayout>;
}
