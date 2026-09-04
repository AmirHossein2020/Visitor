from io import BytesIO

from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse
from rest_framework.test import APITestCase

from apps.accounts.models import User
from apps.subscriptions.models import PlatformAdminAuditLog
from .models import SupportAttachment, SupportMessage, SupportTicket


class SupportAPITests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(email="one@example.com", password="StrongPass123!", full_name="کاربر اول")
        self.other = User.objects.create_user(email="two@example.com", password="StrongPass123!", full_name="کاربر دوم")
        self.admin = User.objects.create_user(email="admin@example.com", password="StrongPass123!", full_name="پشتیبان", is_staff=True)
        self.payload = {"subject": "خطای فاکتور", "category": "order_invoice", "priority": "normal", "description": "فاکتور نمایش داده نمی‌شود."}

    def login(self, user): self.client.force_authenticate(user)
    def create_ticket(self, user=None):
        self.login(user or self.user)
        response = self.client.post("/api/support/tickets/", self.payload, format="json")
        self.assertEqual(response.status_code, 201)
        return SupportTicket.objects.get(pk=response.data["id"])

    def test_authenticated_user_without_subscription_can_create(self):
        ticket = self.create_ticket()
        self.assertTrue(ticket.ticket_number.startswith("SUP-"))
        self.assertEqual(ticket.messages.count(), 1)

    def test_unauthenticated_cannot_create(self):
        self.assertEqual(self.client.post("/api/support/tickets/", self.payload, format="json").status_code, 401)

    def test_owner_isolation_for_list_and_detail(self):
        ticket = self.create_ticket(self.user)
        other_ticket = self.create_ticket(self.other)
        response = self.client.get("/api/support/tickets/")
        self.assertEqual(response.data["count"], 1)
        self.assertEqual(response.data["results"][0]["id"], other_ticket.id)
        self.assertEqual(self.client.get(f"/api/support/tickets/{ticket.id}/").status_code, 404)

    def test_customer_reply_reopens_and_marks_admin_unread(self):
        ticket = self.create_ticket(); ticket.status = "waiting_for_customer"; ticket.admin_unread = False; ticket.save()
        response = self.client.post(f"/api/support/tickets/{ticket.id}/messages/", {"body": "اطلاعات بیشتر"}, format="json")
        self.assertEqual(response.status_code, 201)
        ticket.refresh_from_db(); self.assertEqual(ticket.status, "open"); self.assertTrue(ticket.admin_unread)

    def test_admin_reply_unread_and_audit(self):
        ticket = self.create_ticket(); self.login(self.admin)
        response = self.client.post(f"/api/platform-admin/support/tickets/{ticket.id}/reply/", {"body": "بررسی شد"}, format="json")
        self.assertEqual(response.status_code, 200)
        ticket.refresh_from_db(); self.assertTrue(ticket.customer_unread); self.assertEqual(ticket.status, "waiting_for_customer")
        self.assertTrue(PlatformAdminAuditLog.objects.filter(action="support_reply", target_id=str(ticket.id)).exists())
        self.login(self.user); self.client.get(f"/api/support/tickets/{ticket.id}/"); ticket.refresh_from_db(); self.assertFalse(ticket.customer_unread)

    def test_admin_status_assignment_and_audit(self):
        ticket = self.create_ticket(); self.login(self.admin)
        self.assertEqual(self.client.post(f"/api/platform-admin/support/tickets/{ticket.id}/assign/", {"assigned_admin_id": self.admin.id}, format="json").status_code, 200)
        self.assertEqual(self.client.post(f"/api/platform-admin/support/tickets/{ticket.id}/status/", {"status": "resolved"}, format="json").status_code, 200)
        ticket.refresh_from_db(); self.assertEqual(ticket.assigned_admin, self.admin); self.assertEqual(ticket.status, "resolved")
        self.assertEqual(PlatformAdminAuditLog.objects.filter(target_id=str(ticket.id)).count(), 2)

    def test_internal_note_never_leaks_to_customer(self):
        ticket = self.create_ticket(); self.login(self.admin)
        self.client.post(f"/api/platform-admin/support/tickets/{ticket.id}/internal-note/", {"body": "یادداشت محرمانه"}, format="json")
        self.login(self.user); data = self.client.get(f"/api/support/tickets/{ticket.id}/").data
        self.assertNotIn("یادداشت محرمانه", str(data)); self.assertNotIn("is_internal_note", str(data))

    def test_attachment_private_and_unsafe_rejected(self):
        image = SimpleUploadedFile("shot.png", b"\x89PNG\r\n\x1a\ncontent", content_type="image/png")
        self.login(self.user); response = self.client.post("/api/support/tickets/", {**self.payload, "attachments": [image]}, format="multipart")
        attachment = SupportAttachment.objects.get()
        self.assertEqual(response.status_code, 201); self.assertEqual(self.client.get(f"/api/support/attachments/{attachment.id}/download/").status_code, 200)
        self.login(self.other); self.assertEqual(self.client.get(f"/api/support/attachments/{attachment.id}/download/").status_code, 404)
        bad = SimpleUploadedFile("bad.exe", b"bad", content_type="application/octet-stream")
        self.assertEqual(self.client.post("/api/support/tickets/", {**self.payload, "attachments": [bad]}, format="multipart").status_code, 400)

    def test_closed_history_is_preserved(self):
        ticket = self.create_ticket(); count = ticket.messages.count()
        self.client.post(f"/api/support/tickets/{ticket.id}/close/", {}, format="json")
        ticket.refresh_from_db(); self.assertEqual(ticket.status, "closed"); self.assertIsNotNone(ticket.closed_at); self.assertEqual(ticket.messages.count(), count)

    def test_normal_user_cannot_access_admin_support(self):
        ticket = self.create_ticket();
        self.assertEqual(self.client.get("/api/platform-admin/support/tickets/").status_code, 403)
        self.assertEqual(self.client.post(f"/api/platform-admin/support/tickets/{ticket.id}/status/", {"status": "closed"}, format="json").status_code, 403)

    def test_customer_detail_contract_is_render_safe(self):
        ticket = self.create_ticket()
        response = self.client.get(f"/api/support/tickets/{ticket.id}/")
        self.assertEqual(response.status_code, 200)
        self.assertIsInstance(response.data["messages"], list)
        self.assertIsInstance(response.data["messages"][0]["attachments"], list)
        self.assertNotIn("is_internal_note", response.data["messages"][0])

    def test_admin_detail_contract_allows_null_optional_fields(self):
        ticket = self.create_ticket()
        self.login(self.admin)
        response = self.client.get(f"/api/platform-admin/support/tickets/{ticket.id}/")
        self.assertEqual(response.status_code, 200)
        self.assertIsNone(response.data["assigned_admin"])
        self.assertIsNone(response.data["subscription_summary"])
        self.assertIsInstance(response.data["messages"], list)
        self.assertIsInstance(response.data["messages"][0]["attachments"], list)
