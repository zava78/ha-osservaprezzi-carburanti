class ConfigEntry:
    def __init__(self, data=None, entry_id: str | None = None):
        self.data = data or {}
        self.entry_id = entry_id or "test"
