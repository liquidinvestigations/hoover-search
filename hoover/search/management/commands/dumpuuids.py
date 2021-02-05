import json

from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model


User = get_user_model()


class Command(BaseCommand):

    help = "Dump a JSON dict with username -> UUID mapping"

    def handle(self, **kwargs):
        m = {u.username: u.profile.uuid for u in User.objects.all()}
        print(json.dumps(m))
