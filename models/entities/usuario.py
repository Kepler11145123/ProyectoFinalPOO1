from flask_login import UserMixin  

class Usuario(UserMixin):
    def __init__(self, id, nombre, correo, password, rol='cliente'):
        self.id = id
        self.nombre = nombre
        self.correo = correo
        self.password = password
        self.rol = rol

    def get_id(self):
        return str(self.id)
    
class Cliente(Usuario):
    def __init__(self, id, nombre, correo, password):
        super().__init__(id, nombre, correo, password, 'cliente')

class Administrador(Usuario):
    def __init__(self, id, nombre, correo, password, rol='administrador'):
        super().__init__(id, nombre, correo, password, rol)


# class Usuario(UserMixin):
#     def __init__(self, id_usuario, nombre, correo, contraseña):
#         self.id = id_usuario
#         self.__nombre = nombre
#         self.__correo = correo
#         self.__contraseña = contraseña

#     def get_correo(self):
#         return self.__correo
#     def get_contraseña(self):
#         return self.__contraseña
#     def get_nombre(self):
#         return self.__nombre
    
#     # Método para verificar contraseña
#     def verificar_contraseña(self, contraseña):
#         return self.__contraseña == contraseña 