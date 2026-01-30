from pykeepass import PyKeePass
import os


class KeePassProvider:
    def __init__(self, db_path, master_password):
        self.db_path = db_path
        self.master_password = master_password
        self.kp = None

    def connect(self):
        try:
            self.kp = PyKeePass(self.db_path, password=self.master_password)
            return True, "База KeePass открыта"
        except Exception as e:
            return False, f"Ошибка KeePass: {e}"

    def get_credentials(self, entry_url_or_title):
        if not self.kp:
            return None

        # Ищем запись по URL (часто в поле URL пишут IP роутера) или по заголовку
        entry = self.kp.find_entries(url=entry_url_or_title, first=True)
        if not entry:
            entry = self.kp.find_entries(title=entry_url_or_title, first=True)

        if entry:
            return {
                "username": entry.username,
                "password": entry.password,
                "host": entry.url if entry.url else entry.title
            }
        return None