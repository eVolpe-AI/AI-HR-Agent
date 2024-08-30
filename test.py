import mysql.connector
from mysql.connector import Error


def run():
    try:
        connection = mysql.connector.connect(
            host="voicebot.int1.evolpe.net",
            user="root",
            password="t4jn3h4slo",
            port="3537",
        )
    except Error:
        return f"Coudn't connect to the database. can't get the availibility"

    try:
        cursor = connection.cursor()
        cursor.execute("USE minthcm")
        cursor.execute(
            """SELECT name, date_start, date_end 
               FROM meetings 
               WHERE id IN (
                   SELECT meeting_id FROM meetings_users where user_id = 1
               ) AND date_start > '2024-08-01'
                AND date_end < '2024-08-31'"""
        )
        users = cursor.fetchall()
        cursor.close()
    except Error:
        return f"Error while fetching data from database"

    return users


if __name__ == "__main__":
    users = run()

    meetings_table = []
    meetings_table.append(f"Meeting name - Start date - End date")
    for user in users:
        meetings_table.append(f"{user[0]} - {user[1]} - {user[2]}")

    print("\n".join(meetings_table))
