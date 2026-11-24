from django.core.management.base import BaseCommand
from scorebrowser.models import User
from scorebrowser.synchronization import SynchronizationOutcome, synchronize


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument('username', type=str)

    def handle(self, *args, **options):
        username = options['username']
        print(f"Synchronizing scores for username {username}")

        user = User.objects.get(django_user__username=username)
        result = synchronize(user)
        if result.outcome == SynchronizationOutcome.SYNCHRONIZED:
            print(
                f"Synchronized: {result.new_scores} new, "
                f"{result.superseded_scores} superseded, "
                f"{result.corrected_fields} corrected fields"
            )
        elif result.outcome == SynchronizationOutcome.ALREADY_RUNNING:
            print("Synchronization already in progress.")
        elif result.outcome == SynchronizationOutcome.REAUTH_REQUIRED:
            print("Need to re-link 3icecream.")
        elif result.outcome == SynchronizationOutcome.UPSTREAM_ERROR:
            print(f"Upstream error {result.status_code}: {result.error_body}")
