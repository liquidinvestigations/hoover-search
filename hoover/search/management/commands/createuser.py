from django.core.management.base import BaseCommand
from django.contrib.auth.models import User


class Command(BaseCommand):
    help = "Add a user."

    def add_arguments(self, parser):
        parser.add_argument('username')

    def handle(self, *args, **options):
        username = options['username']
        if User.objects.filter(username=username).exists():
            print("A user with this name already exists!")
            return
        User.objects.create_user(username)
        print("Created Hoover user " + options['username'] + ".")
