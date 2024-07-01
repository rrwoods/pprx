from django.contrib.auth.tokens import PasswordResetTokenGenerator
import six

class AccountActivationTokenGenerator(PasswordResetTokenGenerator):
	def _make_hash_value(self, user, timestamp):
		return six.text_type(user.pk) + six.text_type(timestamp) + six.text_type(user.is_active)

ACCOUNT_ACTIVATION_TOKEN_GENERATOR = AccountActivationTokenGenerator()