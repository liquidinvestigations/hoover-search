import pytest

@pytest.fixture()
def skip_twofactor(monkeypatch):
    monkeypatch.setattr(
        'hoover.contrib.twofactor.middleware.RequireAuth.process_request',
        lambda self, request: None
    )

