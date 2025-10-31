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
    def __init__(self, id, nombre, correo, password):
        super().__init__(id, nombre, correo, password, 'administrador')
