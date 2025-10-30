from django.test import SimpleTestCase
from unittest.mock import patch

from .forms import UserRegistrationForm


class UserRegistrationFormTests(SimpleTestCase):
    def test_clean_email_fails_when_email_already_registered(self):
        data = {'username': 'u', 'email': 'e@example.com', 'password1': 'pwsecure', 'password2': 'pwsecure'}
        with patch('pprxweb.scorebrowser.forms.DjangoUser.objects') as mock_objs:
            mock_objs.filter.return_value.exists.return_value = True
            form = UserRegistrationForm(data=data)
            self.assertFalse(form.is_valid())
            self.assertIn('email', form.errors)

    def test_clean_email_allows_new_email(self):
        data = {'username': 'u2', 'email': 'new@example.com', 'password1': 'pwsecure', 'password2': 'pwsecure'}
        with patch('pprxweb.scorebrowser.forms.DjangoUser.objects') as mock_objs:
            mock_objs.filter.return_value.exists.return_value = False
            form = UserRegistrationForm(data=data)
            # may still be invalid for other reasons (password strength), but we assert email-specific behaviour
            # calling full_clean to trigger clean_email explicitly
            form.full_clean()
            self.assertNotIn('email', form.errors)
