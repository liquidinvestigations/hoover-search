import pytest
from django.dispatch import receiver


@pytest.fixture()
def skip_twofactor(monkeypatch):
    monkeypatch.setattr(
        'hoover.contrib.twofactor.middleware.RequireAuth.process_request',
        lambda self, request: None
    )


@pytest.yield_fixture()
def listen():
    funcs = []

    def listen(signal):
        events = []
        @receiver(signal)
        def listener(sender, **kwargs):
            events.append({k: kwargs[k] for k in kwargs
                           if k in signal.providing_args})
        funcs.append(listener)
        return events

    yield listen
