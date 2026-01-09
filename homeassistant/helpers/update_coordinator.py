class UpdateFailed(Exception):
    pass


class DataUpdateCoordinator:
    def __init__(self, hass, logger, name: str = None, update_interval=None):
        self.hass = hass
        self.logger = logger
        self.name = name
        self.update_interval = update_interval
        self.data = None
        self.last_update_success = True

    async def async_request_refresh(self):
        return True

    """RIMOSSO: placeholder per lo shim update_coordinator.

    Questo modulo era uno stub semplificato per i test locali e non è più
    incluso nel repository. Usare `homeassistant.helpers.update_coordinator`
    reale o fornire mock nei test.
    """
