"""
Script to add data in db
"""
import sqlite3

from passlib.context import CryptContext

from stargazer.main import get_password_hash

users = [
    {"login": "user1", "password": "password1"},
    {"login": "user2", "password": "password2"},
]


con = sqlite3.connect("../database.sqlite3")
cur = con.cursor()

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
for user in users:
    login = user.get("login")
    pwd = get_password_hash(user.get("password"))
    query = (
        f"INSERT INTO users('username','email','full_name','disabled', 'hashed_password') "
        f"VALUES ('{login}', '{login}@stargazer.com', '{login}_{login}', false, '{pwd}');"
    )
    con.execute(query)
    con.commit()
