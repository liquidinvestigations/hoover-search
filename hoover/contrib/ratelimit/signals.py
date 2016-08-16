from django.dispatch import Signal

rate_limit_exceeded = Signal(['counter', 'request'])
