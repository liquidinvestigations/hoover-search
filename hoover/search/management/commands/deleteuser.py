from django.core.management.base import BaseCommand
from django.contrib.auth.models import User


class Command(BaseCommand):
    help = "Delete a user."

    def add_arguments(self, parser):
        parser.add_argument('username')

    def handle(self, *args, **options):
        username = options['username']
        if not User.objects.filter(username=username).exists():
            print(f'No user with the username: {username} ')
            return
        u = User.objects.get(username=username)
        u.delete()
        print(f'Deleted Hoover user: {username}.')
