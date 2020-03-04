from django.core.management.base import BaseCommand
from django.db.migrations.executor import MigrationExecutor
from django.db import connections, DEFAULT_DB_ALIAS


def is_database_synchronized():
    connection = connections[DEFAULT_DB_ALIAS]
    connection.prepare_database()
    executor = MigrationExecutor(connection)
    targets = executor.loader.graph.leaf_nodes()
    return False if executor.migration_plan(targets) else True


class Command(BaseCommand):
    help = "Check service health: migrations, dependencies"

    def handle(self, **options):
        assert is_database_synchronized(), 'Migrations not run'
        print('database ok')
