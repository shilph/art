import base64

import cryptography.fernet
from cryptography.fernet import Fernet
import sqlite3
from datetime import date
from os.path import exists


class ARTDatebaseSQLite3(object):
    DEFAULT_DATABASE = "ARTDB.db"

    AWARD_REQUIRED_FILED_SPLITER = "; ;"

    # ART supports 3 reward program categories: CC, airlines & hotels
    AWARD_CATEGORIES = ["Credit Cards", "Airlines", "Hotels"]

    # Information about each supported Award programs. Those data will be stored in Awards table.
    # Columns: category, award name, expired in months, web crawling script (in awards directory),
    #          required field names & required field labels
    # Note: required field names & required field labels may contain more than one field.
    #       Use AWARD_REQUIRED_FILED_SPLITER to separate.
    AWARD_PROGRAMS = [
        [
            "Credit Cards", "Chase Ultimate Rewards", 0, "", "chase",
            AWARD_REQUIRED_FILED_SPLITER.join(["username", "password"]),
            AWARD_REQUIRED_FILED_SPLITER.join(["Username", "Password"])
        ],
        [
            "Credit Cards", "Amex Membership Rewards", 0, "", "amex",
            AWARD_REQUIRED_FILED_SPLITER.join(["username", "password"]),
            AWARD_REQUIRED_FILED_SPLITER.join(["Username", "Password"])
        ],
        ["Credit Cards", "Bilt", 0, "", "bilt", "email", "Email"],
        [
            "Hotels", "Marriott Bonvoy", 24, "", "marriott",
            AWARD_REQUIRED_FILED_SPLITER.join(["username", "password"]),
            AWARD_REQUIRED_FILED_SPLITER.join(["Username", "Password"])
        ],
        [
            "Hotels", "Hilton Honors", 24, "", "hilton",
            AWARD_REQUIRED_FILED_SPLITER.join(["username", "password"]),
            AWARD_REQUIRED_FILED_SPLITER.join(["Username", "Password"])
        ],
        [
            "Hotels", "Hyatt (World of Hyatt)", 24, "", "hyatt",
            AWARD_REQUIRED_FILED_SPLITER.join(
                ["username", "password", "lastname"]),
            AWARD_REQUIRED_FILED_SPLITER.join(
                ["Username or Membership Number", "Password", "Last Name"])
        ],
        [
            "Airlines", "Delta Skymiles", 0, "", "delta",
            AWARD_REQUIRED_FILED_SPLITER.join(["username", "password"]),
            AWARD_REQUIRED_FILED_SPLITER.join(["Username", "Password"])
        ],
        [
            "Airlines", "United MileagePlus", 0, "", "ua",
            AWARD_REQUIRED_FILED_SPLITER.join(["username", "password"]),
            AWARD_REQUIRED_FILED_SPLITER.join(["Username", "Password"])
        ],
        [
            "Airlines", "American Airlines AAdvantage", 24, "", "aa",
            AWARD_REQUIRED_FILED_SPLITER.join(
                ["username", "password", "lastname"]),
            AWARD_REQUIRED_FILED_SPLITER.join(
                ["Username", "Password", "Last Name"])
        ],
        [
            "Airlines", "Southwest Rapid Rewards", 0, "", "southwest",
            AWARD_REQUIRED_FILED_SPLITER.join(["username", "password"]),
            AWARD_REQUIRED_FILED_SPLITER.join(["Username", "Password"])
        ],
        [
            "Airlines", "Alaska Airlines Mileage Plan", 0, "", "alaska",
            AWARD_REQUIRED_FILED_SPLITER.join(["username", "password"]),
            AWARD_REQUIRED_FILED_SPLITER.join(["Mileage Plan #", "Password"])
        ],
        [
            "Airlines", "Virgin Atlantic Flying Club", 0, "", "virgin_atlantic",
            AWARD_REQUIRED_FILED_SPLITER.join(["username", "password"]),
            AWARD_REQUIRED_FILED_SPLITER.join(["Username", "Password"])
        ],
        [
            "Airlines", "Korean Air SkyPass", 120, "", "korean_air",
            AWARD_REQUIRED_FILED_SPLITER.join(["username", "password"]),
            AWARD_REQUIRED_FILED_SPLITER.join(["Username", "Password"])
        ],
        [
            "Airlines", "Avianca LifeMiles", 12,
            "Expire in 24 months for elite members or accrued via a co-branded card.",
            "avianca",
            AWARD_REQUIRED_FILED_SPLITER.join(["username", "password"]),
            AWARD_REQUIRED_FILED_SPLITER.join(["Username", "Password"])
        ],
    ]

    # configurations/settings
    VERIFY_PASSWORD = "Verify_Password"
    CONFIGS = [
        ["chrome_executable", "Chrome Executable Link", r"C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe"],
        ["art_blog_link", "", "https://automatedrewardstracker.blogspot.com/"],
        ["last_day_note_opened", "", date.today()],
    ]

    def get_str_fixed_length(self, string: str, total_length: int = 32) -> str:
        """Ensure that the string has a fixed length.
        If it's shorter than the desired length, pad it with itself until it reaches the total length.
        If it's longer, truncate it.

        :param string: The input string to be modified.
        :param total_length: The desired total length of the string.
        :return: The modified string with the desired length.
        """
        if len(string) < total_length:
            string += self.get_str_fixed_length(string, total_length - len(string))
        else:
            string = string[:total_length]
        return string

    def encode_str(self, string: str) -> str:
        """Encrypt the input string using the cipher suite.

        :param string: The input string to be encrypted.
        :return: The encrypted string (str type)
        """
        return self.cipher_suite.encrypt(string.encode()).decode()

    def decode_str(self, string: bytes) -> str:
        """Decrypt the input bytes using the cipher suite.

        :param string: The input encrypted bytes.
        :return: The decrypted string.
        """
        return self.cipher_suite.decrypt(string).decode()

    def __init__(self, password: str):
        key = base64.urlsafe_b64encode(self.get_str_fixed_length(password).encode())
        self.cipher_suite = Fernet(key)

        first_time_use = not exists(ARTDatebaseSQLite3.DEFAULT_DATABASE)
        self.connection = sqlite3.connect(ARTDatebaseSQLite3.DEFAULT_DATABASE)
        self.cursor = self.connection.cursor()

        if first_time_use:
            self.create_art_database()
        else:
            # verify password
            self.cursor.execute("SELECT conf_value FROM Configs WHERE conf_key='verify_password';")
            try:
                if self.decode_str(string=self.cursor.fetchone()[0]) != ARTDatebaseSQLite3.VERIFY_PASSWORD:
                    raise RuntimeError("Password does not match.")
            except cryptography.fernet.InvalidToken:
                raise RuntimeError("Password is invalid")

    def close(self) -> None:
        """Disconnect MySQL database"""
        self.cursor.close()
        self.connection.close()

    def create_art_database(self) -> None:
        """Add ART database and tables.

        ART tables
            * Configs: Application configuration/setting
            * Categories: Reward program categories
            * Awards: Reward types and information
            * Accounts: Individual user account per reward program
            * Histories: Reward points histories
        """
        # Configuration
        self.cursor.execute(
            "CREATE TABLE IF NOT EXISTS Configs ("
            "   conf_key TEXT NOT NULL UNIQUE,"
            "   conf_label TEXT,"
            "   conf_value TEXT"
            ")"
        )
        # Award program category: index, category type (credit cards, airlines, hotels..)
        self.cursor.execute(
            "CREATE TABLE IF NOT EXISTS Categories ("
            "   id INTEGER PRIMARY KEY AUTOINCREMENT,"
            "   category TEXT NOT NULL UNIQUE"
            ")"
        )
        # Award program: index, category index, award program name, points expired in months (0 for not expire),
        #                additional note, script to crawl data, required field variable names,
        #                required field variable labels
        self.cursor.execute(
            "CREATE TABLE IF NOT EXISTS Awards ("
            "   id INTEGER PRIMARY KEY AUTOINCREMENT,"
            "   category_id INTEGER NOT NULL,"
            "   award TEXT NOT NULL UNIQUE,"
            "   expire INTEGER NOT NULL, note TEXT,"
            "   script TEXT,"
            "   required_field_names TEXT NOT NULL,"
            "   required_field_displays TEXT NOT NULL,"
            "   FOREIGN KEY (category_id) REFERENCES Categories(id)"
            ")"
        )
        # Account: index, award index, name of a user, required field variable values for Award.required_field_names,
        #          expected expire date of this reward
        self.cursor.execute(
            "CREATE TABLE IF NOT EXISTS Accounts ("
            "   id INTEGER PRIMARY KEY AUTOINCREMENT,"
            "   award_id INTEGER NOT NULL,"
            "   user TEXT NOT NULL,"
            "   required_values TEXT NOT NULL,"
            "   expected_expire TEXT DEFAULT NULL,"
            "   FOREIGN KEY (award_id) REFERENCES Awards(id)"
            ")"
        )
        # Balance history: account index, point balance, date added
        self.cursor.execute(
            "CREATE TABLE IF NOT EXISTS Histories ("
            "   account_id INTEGER NOT NULL,"
            "   balance INTEGER NOT NULL,"
            "   updated TEXT NOT NULL,"
            "   FOREIGN KEY (account_id) REFERENCES Accounts(id)"
            ")"
        )
        # add configs
        for conf_key, conf_label, conf_value in self.CONFIGS:
            self.cursor.execute(
                f"INSERT INTO Configs (conf_key, conf_label, conf_value) "
                f"VALUES  ('{conf_key}', '{conf_label}', '{conf_value}')"
            )
            self.connection.commit()
        # encode a string to verify password
        self.cursor.execute(
            f"INSERT INTO Configs (conf_key, conf_label, conf_value) "
            f"VALUES  ('verify_password', '', '{self.encode_str(ARTDatebaseSQLite3.VERIFY_PASSWORD)}')"
        )
        self.connection.commit()
        # add award categories
        for category in self.AWARD_CATEGORIES:
            self.cursor.execute(
                f"INSERT INTO Categories (category) VALUES ('{category}')"
            )
            self.connection.commit()
        # add known award programs
        for category, award, expire, note, script, required_field_names, required_field_displays in self.AWARD_PROGRAMS:
            self.cursor.execute(
                f"INSERT INTO Awards ("
                f"  category_id, award, expire, note, script, required_field_names, required_field_displays"
                f") VALUES ("
                f"  (SELECT id FROM Categories WHERE category =  '{category}'),"
                f"  '{award}', {expire}, '{note}', '{script}', '{required_field_names}', '{required_field_displays}'"
                f")"
            )
            self.connection.commit()

    def get_configs(self, conf_key: str = None) -> dict:
        """Get data from Configs table.

        :param conf_key: Configs.conf_key to find. If conf_key is null, return all data in Configs
        :return: {conf_key: {conf_label, conf_value} ...}
        """
        self.cursor.execute(
            "SELECT conf_key, conf_label, conf_value FROM Configs" +
            ("" if conf_key is None else f" WHERE conf_key='{conf_key}'")
        )
        configs = {}
        for conf_key, conf_label, conf_value in self.cursor.fetchall():
            configs[conf_key] = {"conf_label": conf_label, "conf_value": conf_value}
        return configs

    def set_config(self, conf_key: str = None, conf_value: str = None) -> None:
        """Set a configuration in Configs.

        :param conf_key: Configs.conf_key to update
        :param conf_value: Configs.conf_key to be updated
        """
        self.cursor.execute(f"UPDATE Configs SET conf_value = '{conf_value}' WHERE conf_key = '{conf_key}'")
        self.connection.commit()

    def get_users(self) -> [str]:
        """Get name of all users.

        :return: name of all users in list
        """
        self.cursor.execute("SELECT DISTINCT user FROM Accounts")
        return [row[0] for row in self.cursor.fetchall()]

    def remove_user(self, user: str) -> None:
        """Remove a user by name. It will remove all award information of the user.

        :param user: name of user to remove
        """
        self.cursor.execute(
            f"DELETE FROM Histories WHERE account_id IN (SELECT id from Accounts WHERE user = '{user}')"
        )
        self.connection.commit()
        self.cursor.execute(f"DELETE FROM Accounts WHERE user = '{user}'")
        self.connection.commit()

    def get_award_info(self, award: str) -> dict | None:
        """Get award information by name of award.

        :param award: name of award to get
        :return: {expire, note, script, required_field_names, required_field_displays}
        """
        self.cursor.execute(
            f"SELECT expire, note, script, required_field_names, required_field_displays "
            f"FROM Awards "
            f"WHERE award = '{award}'"
        )
        result = self.cursor.fetchone()
        if result is None:
            return None
        return {
            "expire": result[0],
            "note": result[1],
            "script": result[2],
            "required_field_names": result[3].split(self.AWARD_REQUIRED_FILED_SPLITER),
            "required_field_displays": result[4].split(self.AWARD_REQUIRED_FILED_SPLITER)
        }

    def get_award_program_names(self) -> [str]:
        """Get all available award program names.

        :return: list of award program names
        """
        self.cursor.execute(
            "SELECT A.award, C.category "
            "FROM Awards A JOIN Categories C ON A.category_id = C.id "
            "ORDER BY C.category, A.award"
        )
        return [f"{award[1]}: {award[0]}" for award in self.cursor.fetchall()]

    def _get_award_id(self, award: str):
        """Get award index by award name.

        :param award: name of award to search
        :return: award index in Award table
        """
        self.cursor.execute(f"SELECT id FROM Awards WHERE award = '{award}'")
        result = self.cursor.fetchone()
        if result is None:
            raise RuntimeError(f"Could not find an award program: {award}")
        return result[0]

    def get_account_info(self, user: str, award: str, username: str) -> dict | None:
        """Get award account information for a user."""
        self.cursor.execute(
            f"SELECT AC.id, AW.required_field_names, AC.required_values, AC.expected_expire "
            f"FROM Accounts AC JOIN Awards AW ON AC.award_id = AW.id "
            f"WHERE "
            f"  AC.user = '{user}'"
            f"  AND AW.award = '{award}'"
        )
        results = self.cursor.fetchall()
        if len(results) == 0:
            return None
        result = next(
            (r for r in results if username in self.decode_str(r[2]).split(self.AWARD_REQUIRED_FILED_SPLITER)),
            None
        )
        if result is None:
            return None
        account_info = {"id": int(result[0]), "expected_expire": result[3]}
        for name, value in zip(
                result[1].split(self.AWARD_REQUIRED_FILED_SPLITER),
                self.decode_str(result[2]).split(self.AWARD_REQUIRED_FILED_SPLITER)
        ):
            account_info[name.strip()] = value.strip()
        return account_info

    def _get_account_id(self, award: str, user: str, username: str):
        """Get account index"""
        award_id = self._get_award_id(award=award)
        self.cursor.execute(
            f"SELECT id, required_values FROM Accounts "
            f"WHERE"
            f"  user = '{user}'"
            f"  AND award_id = {award_id}"
        )
        results = self.cursor.fetchall()
        if len(results) == 0:
            raise RuntimeError(f"Could not find an account for {user} ({award})")
        result = next(
            (r for r in results if username in self.decode_str(r[1]).split(self.AWARD_REQUIRED_FILED_SPLITER)),
            None
        )
        if result is None:
            raise RuntimeError(f"Could not find an account for {user} ({award})")
        return result[0]

    def add_account(self, user: str, award: str, username: str, account_info: dict) -> bool:
        """Add an account."""
        award_id = self._get_award_id(award=award)
        account_info_dict = [account_info[info] for info in account_info if info != "award" and info != "first_field"]
        required_values = self.encode_str(self.AWARD_REQUIRED_FILED_SPLITER.join(account_info_dict))
        if self.get_account_info(award=award, user=user, username=username) is not None:
            return len(self.get_balance_history(user=user, award=award, username=username)) == 0
        self.cursor.execute(
            f"INSERT INTO Accounts (award_id, user, required_values) "
            f"VALUES ({award_id}, '{user}', '{required_values}')"
        )
        self.connection.commit()
        return True

    def get_all_latest_balances(self, user: str) -> dict:
        """Get account balances from a user."""
        balances = {}
        self.cursor.execute(
            f"SELECT C.category, A.award, ACC.required_values, H.balance, ACC.expected_expire, H.updated "
            f"FROM Accounts ACC "
            f"JOIN Awards A ON ACC.award_id = A.id "
            f"JOIN Histories H ON ACC.id = H.account_id "
            f"JOIN Categories C ON A.category_id = C.id "
            f"JOIN "
            f"    (SELECT account_id, MAX(updated) AS max_date FROM Histories GROUP BY account_id) H2 "
            f"    ON H.account_id = H2.account_id AND H.updated = H2.max_date "
            f"WHERE ACC.user = '{user}' "
            f"ORDER BY C.id, A.award"
        )
        results = self.cursor.fetchall()
        for category, award, required_values, balance, expected_expire, updated_date in results:
            if category not in balances:
                balances[category] = []
            if expected_expire is None:
                expected_expire = "Do not expire"
            username = self.decode_str(required_values).split(self.AWARD_REQUIRED_FILED_SPLITER)[0].strip()
            balances[category].append([award, username, balance, expected_expire, updated_date])
        return balances

    def add_balance(self, user: str, award: str, username: str, balance: int, expire_date: date) -> None:
        """Add new award program balance."""
        account_id = self._get_account_id(award=award, user=user, username=username)
        if expire_date is not None:
            self.cursor.execute(
                f"UPDATE Accounts SET expected_expire = '{expire_date}' WHERE id = {account_id}"
            )
            self.connection.commit()

        today = date.today().strftime("%Y-%m-%d")
        self.cursor.execute(
            f"SELECT * FROM Histories WHERE account_id = {account_id} AND updated = '{today}'"
        )
        result = self.cursor.fetchone()

        if result is None:
            self.cursor.execute(
                f"INSERT INTO Histories (account_id, balance, updated) VALUES ({account_id}, {balance}, '{today}')"
            )
            self.connection.commit()
        else:
            self.cursor.execute(
                f"UPDATE Histories SET balance = {balance} WHERE account_id = {account_id} AND updated = '{today}'"
            )
            self.connection.commit()

    def get_balance_history(self, user: str, award: str, username: str, limit: int = 10) -> [[date, int]]:
        """Get Point balance for the last X record (Order by date DESC)."""
        account_id = self._get_account_id(award=award, user=user, username=username)
        self.cursor.execute(
            f"SELECT updated, balance FROM Histories "
            f"WHERE account_id = {account_id} "
            f"ORDER BY updated DESC LIMIT {limit}"
        )
        results = self.cursor.fetchall()
        return [[result[0], result[1]] for result in results]