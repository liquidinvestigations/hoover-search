import pytest
from django.dispatch import receiver


@pytest.yield_fixture()
def listen():
    funcs = []

    def listen(signal):
        events = []

        @receiver(signal)
        def listener(sender, **kwargs):
            events.append({k: kwargs[k] for k in kwargs})
        funcs.append(listener)
        return events

    yield listen
