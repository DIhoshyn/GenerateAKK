import paramiko
import os


class MikroTikSSH:
    def __init__(self, hostname, username, password, port=22):
        self.hostname = hostname
        self.username = username
        self.password = password
        self.port = port
        self.client = None

    def connect(self):
        try:
            self.client = paramiko.SSHClient()
            self.client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            self.client.connect(
                hostname=self.hostname,
                username=self.username,
                password=self.password,
                port=self.port,
                timeout=10
            )
            return True, "Успешное подключение"
        except Exception as e:
            return False, f"Ошибка подключения: {e}"

    def upload_and_run(self, local_path, remote_filename="import.rsc"):
        if not self.client:
            return False, "Нет активного соединения"

        try:
            # Используем SFTP для загрузки файла
            sftp = self.client.open_sftp()
            sftp.put(local_path, remote_filename)
            sftp.close()

            # Выполняем импорт
            # /import блокирует терминал, пока не закончит
            stdin, stdout, stderr = self.client.exec_command(f"/import {remote_filename}")

            # Читаем вывод, чтобы понять, были ли ошибки внутри MikroTik
            out = stdout.read().decode().strip()
            err = stderr.read().decode().strip()

            # Удаляем временный файл после импорта
            self.client.exec_command(f"/file remove {remote_filename}")

            if "Script file loaded and executed successfully" in out or not err:
                return True, "Скрипт успешно выполнен на MikroTik"
            else:
                return False, f"Ошибка при выполнении: {out} {err}"

        except Exception as e:
            return False, f"Ошибка передачи/выполнения: {e}"
        finally:
            self.client.close()