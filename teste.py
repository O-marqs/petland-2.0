import bcrypt

# A senha que você deseja hashear
password = "1"

# Gera um novo hash
hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())

print(hashed_password)
