from werkzeug.security import check_password_hash
from models.entities.usuario import Usuario, Cliente, Administrador

class UserModel:

    @classmethod
    def get_by_id(cls, db_connection, user_id):
        """Obtiene un usuario por su ID"""
        try:
            cursor = db_connection.cursor()
            cursor.execute("SELECT id, nombre, correo, contraseña, rol FROM usuarios WHERE id = %s", (user_id,))
            row = cursor.fetchone()
            cursor.close()
            
            if row:
                if row[4] == 'administrador':
                    return Administrador(row[0], row[1], row[2], row[3], row[4])
                else:
                    return Cliente(row[0], row[1], row[2], row[3], row[4])
            return None
        except Exception as ex:
            raise Exception(f"Error al obtener usuario: {ex}")

    @classmethod
    def login(cls, db_connection, user_entity):
        """Verifica credenciales y devuelve el usuario autenticado"""
        try:
            cursor = db_connection.cursor()
            cursor.execute("SELECT id, nombre, correo, contraseña, rol FROM usuarios WHERE correo = %s", (user_entity.correo,))
            row = cursor.fetchone()
            cursor.close()
            
            if row and check_password_hash(row[3], user_entity.password):
                if row[4] == 'administrador':
                    return Administrador(row[0], row[1], row[2], row[3], row[4])
                else:
                    return Cliente(row[0], row[1], row[2], row[3], row[4])
            return None
        except Exception as ex:
            raise Exception(f"Error en login: {ex}")

    @classmethod
    def create_user(cls, db_connection, new_user_entity):
        """Registra un nuevo usuario en la base de datos"""
        try:
            cursor = db_connection.cursor()
            cursor.execute("SELECT * FROM usuarios WHERE correo = %s", (new_user_entity.correo,))
            if cursor.fetchone():
                raise Exception("El correo electrónico ya está registrado.")
            
            sql_query = "INSERT INTO usuarios (nombre, correo, contraseña, rol) VALUES (%s, %s, %s, %s)"
            datos = (
                new_user_entity.nombre,
                new_user_entity.correo,
                new_user_entity.password, # La contraseña ya debe venir con hash
                'cliente'
            )
            cursor.execute(sql_query, datos)
            db_connection.commit()
            cursor.close()
            return True
        except Exception as ex:
            db_connection.rollback()
            raise ex

    @classmethod
    def update_password(cls, db_connection, user_entity):
        """Actualiza la contraseña de un usuario"""
        try:
            cursor = db_connection.cursor()
            sql_query = "UPDATE usuarios SET contraseña = %s WHERE correo = %s"
            datos = (user_entity.password, user_entity.correo) # La contraseña ya viene con hash
            
            cursor.execute(sql_query, datos)
            db_connection.commit()
            cursor.close()
            return True
        except Exception as ex:
            db_connection.rollback()
            raise Exception(f"Error al actualizar la contraseña: {ex}")

