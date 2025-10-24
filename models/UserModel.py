from werkzeug.security import check_password_hash
from .entities.usuario import Usuario

class UserModel:

    @classmethod
    def get_by_id(cls, db_connection, user_id):
        try:
            cursor = db_connection.cursor()
            cursor.execute("SELECT * FROM usuarios WHERE id = %s", (user_id,))
            row = cursor.fetchone()
            if row:
                return Usuario(row[0], row[1], row[2], row[3], row[4])
            else:
                return None
        except Exception as ex:
            raise Exception(ex)