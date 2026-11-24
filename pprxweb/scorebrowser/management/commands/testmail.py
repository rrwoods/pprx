from django.conf import settings
from django.core.management.base import BaseCommand
from django.core.mail import send_mail

class Command(BaseCommand):
	def handle(self, *args, **options):
		send_mail(
			"PPR X test message!",
			"Here is the message.",
			"pprx.gg@gmail.com",
			[settings.MAINTAINER_EMAIL],
			fail_silently=False,
		)