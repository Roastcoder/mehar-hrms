"""
Simple email backend fallback
"""
from django.core.mail.backends.smtp import EmailBackend as DjangoEmailBackend
from django.conf import settings
import logging

logger = logging.getLogger(__name__)

class SimpleEmailBackend(DjangoEmailBackend):
    """
    Simple email backend that falls back to Django's default SMTP backend
    """
    
    def __init__(self, *args, **kwargs):
        super().__init__(
            host=getattr(settings, 'EMAIL_HOST', 'localhost'),
            port=getattr(settings, 'EMAIL_PORT', 25),
            username=getattr(settings, 'EMAIL_HOST_USER', ''),
            password=getattr(settings, 'EMAIL_HOST_PASSWORD', ''),
            use_tls=getattr(settings, 'EMAIL_USE_TLS', False),
            use_ssl=getattr(settings, 'EMAIL_USE_SSL', False),
            timeout=getattr(settings, 'EMAIL_TIMEOUT', None),
            fail_silently=getattr(settings, 'EMAIL_FAIL_SILENTLY', True),
            *args, **kwargs
        )
    
    def send_messages(self, email_messages):
        """
        Send email messages with error handling
        """
        try:
            return super().send_messages(email_messages)
        except Exception as e:
            logger.error(f"Email sending failed: {e}")
            if not getattr(settings, 'EMAIL_FAIL_SILENTLY', True):
                raise
            return 0