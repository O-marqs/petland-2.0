import mysql.connector
from mysql.connector import Error

def create_connection():
    try:
        connection = mysql.connector.connect(
            host="127.0.0.1",
            user='root',
            password='',
            database='petland'
        )
        if connection.is_connected():
            print("Conexão ao MySQL bem-sucedida")
        return connection
    except Error as e:
        print(f"Erro ao conectar ao MySQL: {e}")
        return None

def close_connection(connection):
    if connection.is_connected():
        connection.close()
        print("Conexão ao MySQL encerrada")
