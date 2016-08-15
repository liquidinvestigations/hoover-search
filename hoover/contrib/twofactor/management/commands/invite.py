from django.core.management.base import BaseCommand
from ... import invitations

class Command(BaseCommand):

    help = "Create invitation for user to set up TOTP"

    def add_arguments(self, parser):
        parser.add_argument('username')
        parser.add_argument('--create', action='store_true')

    def handle(self, username, create, **options):
        url = invitations.invite(username, create)
        print(url)
