from flask_login import UserMixin

class Usuario(UserMixin):
    def __init__(self, id, nombre, correo, password, rol):
        self.id = id
        self.nombre = nombre
        self.correo = correo
        self.password = password #Encapsulamiento
        self.rol = rol

    def get_id(self):
        return str(self.id)
    
class Cliente(Usuario):
    def __init__(self, id, nombre, correo, password, rol='cliente'):
        super().__init__(id, nombre, correo, password, rol)
        
class Administrador(Usuario):
    def __init__(self, id, nombre, correo, password, rol='administrador'):
        super().__init__(id, nombre, correo, password, rol)

class Producto:
    def __init__(self, id, nombre, descripcion, precio, stock, nombre_columna_imagen):
        self.id = id
        self.nombre = nombre
        self.descripcion = descripcion
        self.precio = precio
        self.stock = stock
        self.nombre_columna_imagen = nombre_columna_imagen

class Carrito:
    def __init__(self):
        self.items = []
    def agregar_producto(self, producto):
        self.items.append(producto)
    def calcular_total(self):
        return sum([item.precio for item in self.items])