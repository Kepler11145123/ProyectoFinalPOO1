from werkzeug.security import check_password_hash
from models.entities.usuario import Usuario, Cliente, Administrador

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
    
    # models/UserModel.py

# ... (tus métodos get_by_id y login ya están aquí) ...

    @classmethod
    def create_user(cls, db_connection, new_user_entity):
        """
        Registra un nuevo usuario en la base de datos.
        """
        try:
            # Verificar si el correo ya existe
            cursor = db_connection.cursor()
            cursor.execute("SELECT * FROM usuarios WHERE correo = %s", (new_user_entity.correo,))
            if cursor.fetchone():
                raise Exception("El correo electrónico ya está registrado.")

            # Si no existe, proceder con la inserción
            sql_query = "INSERT INTO usuarios (nombre, correo, contraseña, rol) VALUES (%s, %s, %s, %s)"
            # El rol por defecto es 'cliente' al registrarse
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
            raise ex # Re-lanzamos la excepción para que app.py la maneje

    @classmethod
    def update_password(cls, db_connection, user_entity):
        """
        Actualiza la contraseña de un usuario basado en su correo.
        """
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

