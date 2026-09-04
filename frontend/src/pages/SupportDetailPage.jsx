import { useEffect, useState } from "react";
import AppShell from "../components/AppShell";
import { Badge, Button, Card, StatePanel } from "../components/ui";
import { navigate } from "../hooks/useRoute";
import { getErrorMessage } from "../services/api";
import { formatJalaliDateTime } from "../services/jalali";
import { closeTicket, downloadSupportAttachment, getTicket, replyTicket } from "../services/support";

const tone = { open: "brand", in_progress: "warning", waiting_for_customer: "warning", resolved: "success", closed: "neutral" };
const detailError = (error) => error?.status === 404 ? "این درخواست پشتیبانی پیدا نشد." : error?.status === 403 ? "به این درخواست دسترسی ندارید." : getErrorMessage(error);

export default function SupportDetailPage({ ticketId }) {
  const [ticket, setTicket] = useState();
  const [body, setBody] = useState("");
  const [file, setFile] = useState();
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  const load = () => { setError(""); return getTicket(ticketId).then(setTicket).catch((requestError) => { setTicket(null); setError(detailError(requestError)); }); };
  useEffect(() => {
    let active = true;
    setError("");
    getTicket(ticketId)
      .then((result) => { if (active) setTicket(result); })
      .catch((requestError) => { if (active) { setTicket(null); setError(detailError(requestError)); } });
    return () => { active = false; };
  }, [ticketId]);
  const send = async (event) => { event.preventDefault(); setBusy(true); setError(""); try { const data = new FormData(); data.append("body", body); if (file) data.append("attachments", file); setTicket(await replyTicket(ticketId, data)); setBody(""); setFile(null); } catch (requestError) { setError(getErrorMessage(requestError)); } finally { setBusy(false); } };
  const openFile = async (id) => { try { const blob = await downloadSupportAttachment(id); window.open(URL.createObjectURL(blob), "_blank", "noopener"); } catch (requestError) { setError(getErrorMessage(requestError)); } };
  const close = async () => { try { setTicket(await closeTicket(ticket.id)); } catch (requestError) { setError(getErrorMessage(requestError)); } };

  return <AppShell title={ticket?.ticket_number || "درخواست پشتیبانی"} subtitle={ticket?.subject} backPath="/support">
    {error && <StatePanel type="error" title={error} action={<div className="flex flex-wrap gap-2"><Button onClick={load}>تلاش مجدد</Button><Button variant="ghost" onClick={() => navigate("/support")}>بازگشت به پشتیبانی</Button></div>} />}
    {!ticket && !error && <StatePanel title="در حال دریافت گفتگو" />}
    {ticket && <div className="support-thread">
      <Card className="ticket-meta"><div><Badge tone={tone[ticket.status] || "neutral"}>{ticket.status_display}</Badge><h2>{ticket.subject}</h2><p>{ticket.category_display} · اولویت {ticket.priority_display}</p>{ticket.context_label && <p>مرتبط با: {ticket.context_label}</p>}</div>{ticket.status !== "closed" && <Button variant="ghost" onClick={close}>بستن درخواست</Button>}</Card>
      <div className="message-list">{ticket.messages.length === 0 && <StatePanel type="empty" title="هنوز پیامی در این درخواست نیست." />}{ticket.messages.map((message) => <article className={`support-message ${message.sender_role}`} key={message.id ?? `${message.created_at}-${message.body}`}><header><strong>{message.sender_role === "support" ? "پشتیبانی" : message.sender_name}</strong><time>{formatJalaliDateTime(message.created_at)}</time></header><p>{message.body || "—"}</p>{message.attachments.map((attachment) => <button key={attachment.id ?? attachment.original_name} onClick={() => openFile(attachment.id)}>پیوست: {attachment.original_name}</button>)}</article>)}</div>
      {ticket.status !== "closed" && <Card className="reply-box"><form onSubmit={send}><label>پاسخ شما<textarea required value={body} onChange={(event) => setBody(event.target.value)} /></label><div><input type="file" accept="image/jpeg,image/png,image/webp,application/pdf" onChange={(event) => setFile(event.target.files?.[0])} /><Button disabled={busy}>{busy ? "در حال ارسال…" : "ارسال پاسخ"}</Button></div><p>اطلاعات محرمانه یا رمز عبور ارسال نکنید.</p></form></Card>}
    </div>}
  </AppShell>;
}
