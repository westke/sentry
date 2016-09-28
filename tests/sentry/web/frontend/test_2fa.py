from __future__ import absolute_import

from django.core.urlresolvers import reverse

from sentry.testutils import TestCase
from sentry.models import TotpInterface, User


class TwoFactorAuthTestPassword(TestCase):

    def test_security_renders_without_2fa(self):
        User.objects.create(email='a@example.com')
        user = User.objects.get(email='a@example.com')
        self.login_as(user)
        path = reverse('sentry-account-security')
        resp = self.client.get(path)
        assert resp.status_code == 200
        self.assertTemplateUsed('sentry/account/security.html')
        assert 'has_2fa' in resp.context
        assert resp.context['has_2fa'] is False
        self.assertContains(resp, 'Enable')
        User.objects.get(email='a@example.com').delete()

    def test_security_renders_with_2fa(self):
        User.objects.create(email='b@example.com')
        user = User.objects.get(email='b@example.com')
        self.login_as(user)
        TotpInterface().enroll(user)
        path = reverse('sentry-account-security')
        resp = self.client.get(path)
        self.assertTemplateUsed('sentry/account/security.html')
        assert 'has_2fa' in resp.context
        assert resp.context['has_2fa'] is True
        self.assertContains(resp, 'Manage')
        User.objects.get(email='b@example.com').delete()

    def test_2fa_settings_render_without_2fa(self):
        User.objects.create(email='c@example.com')
        user = User.objects.get(email='c@example.com')
        path = reverse('sentry-account-settings-2fa')
        self.login_as(user)
        resp = self.client.get(path)
        assert resp.status_code == 200
        self.assertTemplateUsed('sentry/account/twofactor.html')
        assert 'has_2fa' in resp.context
        assert resp.context['has_2fa'] is False
        self.assertContains(resp, 'Add</button>')
        self.assertContains(resp, 'this can only be managed if 2FA is enabled')
        self.assertNotContains(resp, '<span class="icon-trash">')
        User.objects.get(email='c@example.com').delete()

    def test_2fa_settings_render_with_2fa(self):
        User.objects.create(email='d@example.com')
        user = User.objects.get(email='d@example.com')
        path = reverse('sentry-account-settings-2fa')
        self.login_as(user)
        TotpInterface().enroll(user)
        resp = self.client.get(path)
        assert resp.status_code == 200
        self.assertTemplateUsed('sentry/account/twofactor.html')
        assert 'has_2fa' in resp.context
        assert resp.context['has_2fa'] is True
        self.assertNotContains(resp, 'this can only be managed if 2FA is enabled')
        self.assertContains(resp, '<span class="icon-trash">')
        User.objects.get(email='d@example.com').delete()

    def test_add_2fa_password(self):
        User.objects.create(email='e@example.com')
        user = User.objects.get(email='e@example.com')
        user.set_password('password')
        user.save()
        path = reverse('sentry-account-settings-2fa-totp')
        self.login_as(user)
        resp = self.client.post(path, data={'enroll': ''})
        self.assertContains(resp, 'QR')
        self.assertContains(resp, 'Sentry account password')
        self.assertNotContains(resp, 'Method is currently not enabled')
        User.objects.get(email='e@example.com').delete()

    def test_totp_get_path_render(self):
        User.objects.create(email='f@example.com')
        user = User.objects.get(email='f@example.com')
        path = reverse('sentry-account-settings-2fa-totp')
        self.login_as(user)
        resp = self.client.get(path)
        self.assertNotContains(resp, 'QR')
        self.assertNotContains(resp, 'Sentry account password')
        self.assertContains(resp, 'Method is currently not enabled')
        User.objects.get(email='f@example.com').delete()

    def test_remove_2fa_password(self):
        User.objects.create(email='g@example.com')
        user = User.objects.get(email='g@example.com')
        user.set_password('password')
        user.save()
        TotpInterface().enroll(user)
        path = reverse('sentry-account-settings-2fa-totp')
        self.login_as(user)
        resp = self.client.post(path, data={'remove': ''})
        assert resp.status_code == 200
        self.assertTemplateUsed('sentry/account/twofactor/remove.html')
        self.assertContains(resp, 'Do you want to remove the method?')
        self.assertContains(resp, 'Sentry account password')
        User.objects.get(email='g@example.com').delete()


class TwoFactorAuthTestNoPassword(TestCase):

    def test_add_2fa_SSO(self):
        User.objects.create(email='h@example.com')
        user = User.objects.get(email='h@example.com')
        user.set_unusable_password()
        user.save()
        path = reverse('sentry-account-settings-2fa-totp')
        self.login_as(user)
        resp = self.client.post(path, data={'enroll': ''})
        assert resp.status_code == 200
        self.assertTemplateUsed('sentry/account/twofactor/enroll_totp.html')
        assert 'otp_form' in resp.context
        self.assertContains(resp, 'One-time password')
        self.assertContains(resp, 'Authenticator App')
        self.assertNotContains(resp, 'Sentry account password')
        User.objects.get(email='h@example.com').delete()

    def test_remove_2fa_SSO(self):
        User.objects.create(email='i@example.com')
        user = User.objects.get(email='i@example.com')
        user.set_unusable_password()
        user.save()
        TotpInterface().enroll(user)
        path = reverse('sentry-account-settings-2fa-totp')
        self.login_as(user)
        resp = self.client.post(path, data={'remove': ''})
        assert resp.status_code == 200
        self.assertTemplateUsed('sentry/account/twofactor/remove.html')
        self.assertContains(resp, 'Do you want to remove the method?')
        self.assertNotContains(resp, 'Sentry account password')
        User.objects.get(email='i@example.com').delete()
