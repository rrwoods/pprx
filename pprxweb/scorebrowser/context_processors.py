from django.conf import settings


def staging_context(request):
    email_backend = getattr(settings, 'EMAIL_BACKEND', '')
    webhook_id = getattr(settings, 'WEBHOOK_ID', '')
    sanbai_oauth_redirect_uri = getattr(settings, 'SANBAI_OAUTH_REDIRECT_URI', None)
    return {
        'is_staging': bool(getattr(settings, 'IS_STAGING', False)),
        'EMAIL_BACKEND': email_backend,
        'WEBHOOK_ID': webhook_id,
        'SANBAI_OAUTH_REDIRECT_URI': sanbai_oauth_redirect_uri,
        'staging_email_is_smtp': email_backend == 'django.core.mail.backends.smtp.EmailBackend',
    }
