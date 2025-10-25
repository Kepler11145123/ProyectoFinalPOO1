from werkzeug.security import check_password_hash
from models.entities.usuario import Usuario, Cliente, Administrador

class UserModel:

    # models/UserModel.py
from werkzeug.security import check_password_hash
from models.entities.usuario import Usuario, Cliente, Administrador

class UserModel:

    @classmethod
    def get_by_id(cls, db_connection, user_id):
        """Obtiene un usuario por su ID"""
        try:
            # Usar 'with' es una buena práctica, cierra el cursor automáticamente
            with db_connection.cursor() as cursor:
                cursor.execute("SELECT id, nombre, correo, contraseña, rol FROM usuarios WHERE id = %s", (user_id,))
                row = cursor.fetchone()
            
                if row:
                    if row[4] == 'administrador':
                        return Administrador(row[0], row[1], row[2], row[3])
                    else:
                        return Cliente(row[0], row[1], row[2], row[3])
                return None
        except Exception as ex:
            # ¡IMPORTANTE! Hacer rollback para limpiar la transacción fallida
            db_connection.rollback()
            raise Exception(f"Error al obtener usuario por ID: {ex}")

    @classmethod
    def login(cls, db_connection, user_entity):
        """Verifica credenciales y devuelve el usuario autenticado"""
        try:
            with db_connection.cursor() as cursor:
                cursor.execute("SELECT id, nombre, correo, contraseña, rol FROM usuarios WHERE correo = %s", (user_entity.correo,))
                row = cursor.fetchone()
            
                if row and check_password_hash(row[3], user_entity.password):
                    if row[4] == 'administrador':
                        return Administrador(row[0], row[1], row[2], row[3])
                    else:
                        return Cliente(row[0], row[1], row[2], row[3])
                return None
        except Exception as ex:
            # ¡IMPORTANTE! Hacer rollback aquí también
            db_connection.rollback()
            raise Exception(f"Error en login: {ex}")

    # Los métodos create_user y update_password ya tenían rollback, ¡así que están bien!
    # ... (resto de tus métodos sin cambios si ya tienen rollback)


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
                new_user_entity.password,
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
            datos = (user_entity.password, user_entity.correo)
            
            cursor.execute(sql_query, datos)
            db_connection.commit()
            cursor.close()
            return True
        except Exception as ex:
            db_connection.rollback()
            raise Exception(f"Error al actualizar la contraseña: {ex}")
