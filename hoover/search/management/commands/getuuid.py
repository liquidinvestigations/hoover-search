from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model


User = get_user_model()


class Command(BaseCommand):

    help = "Get the uuid for a given user"

    def add_arguments(self, parser):
        parser.add_argument('username')

    def handle(self, username, **kwargs):
        uuid = User.objects.get(username=username).profile.uuid
        print(uuid)
