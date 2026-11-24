print("Hello, World!")

import mysql.connector
conexao = mysql.connector.connect(
    host="localhost",
    user="root",
    password="root",
    database = "escola"
)

cursor = conexao.cursor()

print("conectado com sucesso!")

sql = "INSERT INTO aluno (nome , email,data_nascimento,curso) values (%s ,%s,%s,%s)"

valores = ("Lucas Silva", "lucas.silva@gmail.com", "1998-04-12", "Manufatura Digital")

cursor.execute(sql, valores)
conexao.commit()
