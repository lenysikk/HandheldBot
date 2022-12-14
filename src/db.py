import sqlite3
import datetime

class Database:
    def __init__(self, db_file):
        self.connection = sqlite3.connect(db_file)
        self.cursor = self.connection.cursor()

    def user_exists(self, user_id):
        with self.connection:
            result = self.cursor.execute("SELECT * FROM `users` WHERE `user_id` = ?", (user_id,)).fetchmany(1)
            return bool(len(result))


    def add_user(self, user_id):
        with self.connection:
            return self.cursor.execute("INSERT INTO `users` (`user_id`) VALUES (?)", (user_id,))

    def set_remind(self, user_id, text_remind, time_date):
        with self.connection:
            return self.cursor.execute("UPDATE `users` SET `text_remind` = ?, `time_date` = ? WHERE `user_id` = ?", (text_remind, time_date, user_id,))

    def get_users_remind(self):
        now = datetime.datetime.now()
        current_time = now.time().strftime("%H:%M")
        with self.connection:
            return self.cursor.execute("SELECT `user_id` AND `text_remind` FROM `users` WHERE `time_date` <= ?", (current_time,)).fetchmany(1)

    async def get_users(self)->list:
        with self.connection:
            return self.cursor.execute("SELECT * FROM `users`").fetchall()

    async def delete_remind(self, user_id):
        with self.connection:
            return self.cursor.execute("UPDATE `users` SET `text_remind` = ?, `time_date` = ? WHERE `user_id` = ?", (None, None, user_id,)).fetchmany(1)

    async def create_note(self, user_id, text):
        with self.connection:
            return self.cursor.execute("UPDATE `users` SET `note` = ? WHERE `user_id` = ?", (text, user_id,))

    async def get_info_by_id(self, user_id):
            with self.connection:
                result = self.cursor.execute("SELECT * FROM `users` WHERE `user_id` = ?", (user_id, )).fetchmany(1)
                return list(result)

    async def set_zodiac(self, user_id, zodiac):
        with self.connection:
            return self.cursor.execute("UPDATE `users` SET `zodiac` = ? WHERE `user_id` = ?", (zodiac, user_id,))

    async def get_zodiac_by_id(self, user_id):
        with self.connection:
            result = self.cursor.execute("SELECT * FROM `users` WHERE `user_id` = ?", (user_id, )).fetchmany(1)
            return list(result)[0][5]

    async def delete_zodiac(self, user_id):
        with self.connection:
            return self.cursor.execute("UPDATE `users` SET `zodiac` = ? WHERE `user_id` = ?", (None, user_id,))