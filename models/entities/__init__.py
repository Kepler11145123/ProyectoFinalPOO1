# Este archivo convierte 'entities' en un paquete Python
# e importa las clases para que sean más fáciles de encontrar.

from .usuario import Usuario, Cliente, Administrador
from .producto import Producto

__all__ = ['Usuario', 'Cliente', 'Administrador', 'Producto']
