import mysql.connector
from datetime import date


class ARTDatabase(object):
    """MySQL database wrapper for ART."""
    DEFAULT_DATABASE = "ARTDB"
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

    def __init__(self, password: str):
        """Initial function. Connected to the local MySQL.

        :param password: password to connect to the MySQL
        """
        # TODO: may need to change connection to non-root user
        try:
            self.connection = mysql.connector.connect(
                host="localhost", user="root", password=password)
        except mysql.connector.errors.ProgrammingError:
            raise RuntimeError("Incorrect password")
        self.cursor = self.connection.cursor()
        self.cursor.execute(f"SHOW DATABASES LIKE '{self.DEFAULT_DATABASE}'")
        if self.cursor.fetchone() is None:
            self.create_art_database()
        else:
            self.cursor.execute(f"USE {self.DEFAULT_DATABASE}")

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
        self.cursor.execute(f"CREATE DATABASE {self.DEFAULT_DATABASE}")
        self.cursor.execute(f"USE {self.DEFAULT_DATABASE}")
        # Configuration
        self.cursor.execute(
            "CREATE TABLE Configs ("
            "   conf_key VARCHAR(50) NOT NULL UNIQUE"
            "   conf_value VARCHAR(300)"
            ")"
        )
        # Award program category: index, category type (credit cards, airlines, hotels..)
        self.cursor.execute(
            "CREATE TABLE Categories ("
            "   id INT AUTO_INCREMENT PRIMARY KEY,"
            "   category VARCHAR(25) NOT NULL UNIQUE"
            ")"
        )
        # Award program: index, category index, award program name, points expired in months (0 for not expire),
        #                additional note, script to crawl data, required field variable names,
        #                required field variable labels
        self.cursor.execute(
            "CREATE TABLE Awards ("
            "   id INT AUTO_INCREMENT PRIMARY KEY,"
            "   category_id INT NOT NULL,"
            "   award VARCHAR(50) NOT NULL UNIQUE,"
            "   expire INT NOT NULL, note VARCHAR(100),"
            "   script VARCHAR(20),"
            "   required_field_names VARCHAR(200) NOT NULL,"
            "   required_field_displays VARCHAR(200) NOT NULL,"
            "   FOREIGN KEY (category_id) REFERENCES Categories(id)"
            ")"
        )
        # Account: index, award index, name of a user, required field variable values for Award.required_field_names,
        #          expected expire date of this reward
        self.cursor.execute(
            "CREATE TABLE Accounts ("
            "   id INT AUTO_INCREMENT PRIMARY KEY,"
            "   award_id INT NOT NULL,"
            "   user VARCHAR(30) NOT NULL,"
            "   required_values VARCHAR(200) NOT NULL,"
            "   expected_expire DATE DEFAULT NULL,"
            "   FOREIGN KEY (award_id) REFERENCES Awards(id)"
            ")"
        )
        # Balance history: account index, point balance, date added
        self.cursor.execute(
            "CREATE TABLE Histories ("
            "   account_id INT NOT NULL,"
            "   balance INT NOT NULL,"
            "   updated DATE NOT NULL,"
            "   FOREIGN KEY (account_id) REFERENCES Accounts(id)"
            ")"
        )
        # add award categories
        for category in self.AWARD_CATEGORIES:
            self.cursor.execute(
                f"INSERT INTO Categories (category) VALUES ('{category}')")
            self.connection.commit()
        # add known award programs
        for category, award, expire, note, script, required_field_names, required_field_displays in self.AWARD_PROGRAMS:
            self.cursor.execute(
                f"INSERT INTO Awards ("
                f"   category_id, award, expire, note, script, required_field_names, required_field_displays"
                f") VALUES ("
                f"  (SELECT id FROM Categories WHERE category = '{category}'),"
                f"  '{award}', {expire}, '{note}', '{script}', '{required_field_names}', '{required_field_displays}'"
                f")"
            )
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
            f"DELETE FROM Histories WHERE account_id IN (SELECT id from Accounts WHERE user = '{user}'"
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
            "SELECT expire, note, script, required_field_names, required_field_displays "
            "FROM Awards "
            f"WHERE award = '{award}'")
        result = self.cursor.fetchone()
        if result is None:
            return None
        return {
            "expire":
                result[0],
            "note":
                result[1],
            "script":
                result[2],
            "required_field_names":
                result[3].split(self.AWARD_REQUIRED_FILED_SPLITER),
            "required_field_displays":
                result[4].split(self.AWARD_REQUIRED_FILED_SPLITER)
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

    def get_account_info(self, user: str, award: str,
                         username: str) -> dict | None:
        """Get award account information for a user.

        :param user: name of user
        :param award: name of award program
        :param username: username or ID
        :return: {id, expected_expire, required_field_names+required_values (split and paired)}
                 or None if there is no account found
        """
        self.cursor.execute(
            f"SELECT AC.id, AW.required_field_names, AC.required_values, AC.expected_expire "
            f"FROM Accounts AC JOIN Awards AW ON AC.award_id = AW.id "
            f"WHERE "
            f"  AC.user = '{user}'"
            f"  AND AW.award = '{award}'"
            f"  AND ("
            f"      AC.required_values LIKE '{username}{self.AWARD_REQUIRED_FILED_SPLITER}%' "
            f"      OR AC.required_values = '{username}'"
            f"  )")
        result = self.cursor.fetchone()
        if result is None:
            return None
        account_info = {"id": int(result[0]), "expected_expire": result[3]}
        for name, value in zip(
                result[1].split(self.AWARD_REQUIRED_FILED_SPLITER),
                result[2].split(self.AWARD_REQUIRED_FILED_SPLITER)):
            account_info[name.strip()] = value.strip()
        return account_info

    def _get_account_id(self, award: str, user: str, username: str):
        """Get account index

        :param award: name of award program
        :param user: name of user
        :param username: username or ID
        :return: Award table index
        """
        award_id = self._get_award_id(award=award)
        self.cursor.execute(
            f"SELECT id FROM Accounts "
            f"WHERE"
            f"  user = '{user}'"
            f"  AND award_id = {award_id}"
            f"  AND ("
            f"      required_values LIKE '{username}{self.AWARD_REQUIRED_FILED_SPLITER}%' "
            f"      OR required_values = '{username}'"
            f"  )"
        )
        result = self.cursor.fetchone()
        if result is None:
            raise RuntimeError(f"Could not find an account for {user} ({award})")
        return result[0]

    def add_account(self, user: str, award: str, username: str,
                    account_info: dict) -> bool:
        """Add an account.

        :param user: name of user
        :param award: award program
        :param username: username or ID
        :param account_info: other account information
        :return: True if added; False if there is an account exists
        """
        award_id = self._get_award_id(award=award)
        account_info_dict = [
            account_info[info]
            for info in account_info
            if info != "award" and info != "first_field"
        ]
        required_values = self.AWARD_REQUIRED_FILED_SPLITER.join(
            account_info_dict)
        if self.get_account_info(
                award=award, user=user, username=username) is not None:
            return False
        self.cursor.execute(
            f"INSERT INTO Accounts (award_id, user, required_values) "
            f"VALUES ({award_id}, '{user}', '{required_values}')"
        )
        self.connection.commit()
        return True

    def get_all_latest_balances(self, user: str) -> dict:
        """Get account balances from a user.

        :param user: name of user
        :return: {category: list of [award program, username, balance, expected expire date, last updated date]}
        """
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
            balances[category].append([
                award,
                required_values.split(
                    self.AWARD_REQUIRED_FILED_SPLITER)[0].strip(), balance,
                expected_expire, updated_date
            ])
        return balances

    def add_balance(self, user: str, award: str, username: str, balance: int,
                    expire_date: date) -> None:
        """Add new award program balance.

        :param user: name of user
        :param award: award program
        :param username: username
        :param balance: new balance
        :param expire_date: expected expire date
        """
        account_id = self._get_account_id(
            award=award, user=user, username=username)
        # update expected expire date
        if expire_date is not None:
            self.cursor.execute(
                f"UPDATE Accounts SET expected_expire = '{expire_date}' WHERE id = {account_id}"
            )
            self.connection.commit()

        # only one record per account/date
        today = date.today()
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

    def get_balance_history(self,
                            user: str,
                            award: str,
                            username: str,
                            limit: int = 10) -> [[date, int]]:
        """Get Point balance for the last X record (Order by date DESC).

        :param user: name of user
        :param award: award program
        :param username: username
        :param limit: number of last histories
        :return: list of [updated date, balance]
        """
        account_id = self._get_account_id(
            award=award, user=user, username=username)
        self.cursor.execute(
            f"SELECT updated, balance FROM Histories "
            f"WHERE account_id = {account_id} "
            f"ORDER BY updated DESC LIMIT {limit}"
        )
        results = self.cursor.fetchall()
        return [[result[0], result[1]] for result in results]
