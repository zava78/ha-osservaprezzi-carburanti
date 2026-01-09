def async_get_clientsession(hass):
    """Return a dummy session object. Not used in tests where network is mocked."""
    class DummySession:
        async def get(self, *args, **kwargs):
            class Resp:
                status = 200

                async def __aenter__(self):
                    return self

                async def __aexit__(self, exc_type, exc, tb):
                    return False

                async def text(self):
                    return ""

                async def json(self):
                    return {}

            return Resp()

    return DummySession()
