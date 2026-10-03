import json
from unittest import mock

from django.test import TestCase, override_settings

from Base.models import Contact
from Base.notify import send_contact_email

ENV = {"RESEND_API_KEY": "re_test", "CONTACT_EMAIL": "me@example.com"}


class SendContactEmailTests(TestCase):
    def setUp(self):
        self.contact = Contact(name="Alice", email="alice@example.com", content="Hello!", number="")

    @mock.patch.dict("os.environ", {}, clear=True)
    @mock.patch("Base.notify.urllib.request.urlopen")
    def test_skipped_when_not_configured(self, urlopen):
        self.assertFalse(send_contact_email(self.contact))
        urlopen.assert_not_called()

    @mock.patch.dict("os.environ", ENV, clear=True)
    @mock.patch("Base.notify.urllib.request.urlopen")
    def test_sends_message_with_reply_to(self, urlopen):
        urlopen.return_value.__enter__.return_value.status = 200

        self.assertTrue(send_contact_email(self.contact))

        request = urlopen.call_args.args[0]
        payload = json.loads(request.data)
        self.assertEqual(request.get_header("Authorization"), "Bearer re_test")
        self.assertEqual(payload["to"], ["me@example.com"])
        self.assertEqual(payload["reply_to"], "alice@example.com")
        self.assertIn("Hello!", payload["text"])

    @mock.patch.dict("os.environ", ENV, clear=True)
    @mock.patch("Base.notify.urllib.request.urlopen", side_effect=TimeoutError)
    def test_failure_does_not_raise(self, urlopen):
        with self.assertLogs("Base.notify", level="ERROR"):
            self.assertFalse(send_contact_email(self.contact))


@override_settings(STORAGES={"staticfiles": {"BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"}})
class ContactViewTests(TestCase):
    @mock.patch("Base.views.send_contact_email")
    def test_valid_submission_saves_and_emails(self, send):
        response = self.client.post("/", {"name": "Alice", "email": "alice@example.com", "content": "Hi", "number": ""})

        self.assertRedirects(response, "/#contact", fetch_redirect_response=False)
        self.assertEqual(Contact.objects.count(), 1)
        send.assert_called_once_with(Contact.objects.get())

    @mock.patch("Base.views.send_contact_email")
    def test_invalid_submission_is_rejected(self, send):
        self.client.post("/", {"name": "A", "email": "alice@example.com", "content": "Hi"})

        self.assertEqual(Contact.objects.count(), 0)
        send.assert_not_called()
