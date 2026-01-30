import pandas as pd
import random
import string
import os


class OVPNGenerator:
    TRANSLIT_MAP = {
        'а': 'a', 'б': 'b', 'в': 'v', 'г': 'g', 'д': 'd', 'е': 'e', 'ё': 'e',
        'ж': 'zh', 'з': 'z', 'и': 'i', 'й': 'y', 'к': 'k', 'л': 'l', 'м': 'm',
        'н': 'n', 'о': 'o', 'п': 'p', 'р': 'r', 'с': 's', 'т': 't', 'у': 'u',
        'ф': 'f', 'х': 'kh', 'ц': 'ts', 'ч': 'ch', 'ш': 'sh', 'щ': 'shch',
        'ы': 'y', 'э': 'e', 'ю': 'yu', 'я': 'ya',
        'ь': '', 'ъ': '', ' ': '_'
    }

    def __init__(self, output_dir="files"):
        self.output_dir = output_dir
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)

    def _translit(self, text):
        if not isinstance(text, str): return ""
        text = text.lower().strip()
        res = "".join(self.TRANSLIT_MAP.get(c, c) for c in text)
        return "".join(c for c in res if c in (string.ascii_lowercase + string.digits + "_."))

    def _generate_password(self, length=20):
        specials = "!@#$%^&*()-_=+[{]};:,.<>/?"
        alphabet = string.ascii_letters + string.digits + specials
        while True:
            pwd = "".join(random.choice(alphabet) for _ in range(length))
            if any(c.isupper() for c in pwd) and any(c in specials for c in pwd):
                return pwd

    def process_excel(self, excel_path, profile="UFD", rsc_filename="mikrotik_ovpn.rsc",
                      txt_filename="credentials.txt"):
        output_path_rsc = os.path.join(self.output_dir, rsc_filename)
        output_path_txt = os.path.join(self.output_dir, txt_filename)

        df = pd.read_excel(excel_path)

        with open(output_path_rsc, "wb") as f_rsc, \
                open(output_path_txt, "w", encoding="utf-8") as f_txt:

            f_rsc.write(b"/ppp secret\n")
            f_txt.write(f"Список аккаунтов OVPN (Profile: {profile}):\n")
            f_txt.write("-" * 50 + "\n")

            for _, row in df.iterrows():
                surname_raw = str(row.get('фамилия', '')).strip()
                name_raw = str(row.get('имя', '')).strip()
                phone_raw = str(row.get('номер тф', '')).strip()
                phone = "".join(filter(lambda x: x.isdigit() or x == '+', phone_raw))

                if not name_raw or not surname_raw: continue

                t_name = self._translit(name_raw)
                t_surname = self._translit(surname_raw)

                login = f"{t_name[0]}.{t_surname}"
                password = self._generate_password()

                safe_comment = f"{t_surname.capitalize()}_{t_name.capitalize()}_{phone}"

                # Динамический профиль
                line = f'add name="{login}" password="{password}" service=ovpn profile={profile} comment="{safe_comment}"\n'
                f_rsc.write(line.encode('ascii', 'ignore'))

                f_txt.write(f"ФИО: {surname_raw} {name_raw}\n")
                f_txt.write(f"Логин: {login}\n")
                f_txt.write(f"Пароль: {password}\n")
                f_txt.write("-" * 30 + "\n")

        return output_path_rsc, output_path_txt