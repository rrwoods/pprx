from django.test import TestCase
from scorebrowser.models import UnlockEvent, UnlockTask, Version


class PPRXTestCase(TestCase):
    fixtures = ['basedata.json']

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()

        # The New Challenge charts (A3+) UnlockTask is the single Catalog row
        # that updatecharts and Synchronization look up by name. Replacing this
        # exception is tracked by #66 and documented in ADR-0005.
        current_version = Version.objects.order_by('id').last()
        unlock_event = UnlockEvent.objects.create(
            name="New Challenge charts (A3)",
            version=current_version,
            group=None,
            ordering=0,
        )
        UnlockTask.objects.create(
            event=unlock_event,
            name="New Challenge charts (A3+)",
            ordering=0,
        )

