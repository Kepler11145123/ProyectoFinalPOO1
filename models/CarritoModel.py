from models.entities.producto import Producto

class CarritoModel:
    @classmethod
    def get_carrito_by_usuario(cls, db_connection, id_usuario):
        """Obtiene todos los items del carrito de un usuario específico"""
        try:
            items_carrito = []
            with db_connection.cursor() as cursor:
                sql = """
                    SELECT c.id_carrito, c.id_producto, p.nombre, p.precio, p.nombre_columna_imagen 
                    FROM carrito c
                    JOIN productos p ON c.id_producto = p.id
                    WHERE c.id_usuario = %s
                """
                cursor.execute(sql, (id_usuario,))
                rows = cursor.fetchall()

                for row in rows:
                    items_carrito.append({
                        'id_carrito': row[0],
                        'id': row[1],  # id_producto
                        'nombre': row[2],
                        'precio': float(row[3]),
                        'imagen': row[4],
                        'cantidad': 1  # Por ahora manejamos cantidad fija de 1
                    })
                return items_carrito
        except Exception as ex:
            db_connection.rollback()
            raise ValueError(f"Error al obtener carrito: {ex}")

    @classmethod
    def agregar_producto(cls, db_connection, id_usuario, id_producto):
        """Agrega un producto al carrito del usuario"""
        try:
            with db_connection.cursor() as cursor:
                sql = "INSERT INTO carrito (id_usuario, id_producto) VALUES (%s, %s)"
                cursor.execute(sql, (id_usuario, id_producto))
                db_connection.commit()
                return True
        except Exception as ex:
            db_connection.rollback()
            raise ValueError(f"Error al agregar producto al carrito: {ex}")

    @classmethod
    def eliminar_producto(cls, db_connection, id_usuario, id_producto):
        """Elimina un producto del carrito del usuario"""
        try:
            with db_connection.cursor() as cursor:
                sql = "DELETE FROM carrito WHERE id_usuario = %s AND id_producto = %s"
                cursor.execute(sql, (id_usuario, id_producto))
                db_connection.commit()
                return True
        except Exception as ex:
            db_connection.rollback()
            raise ValueError(f"Error al eliminar producto del carrito: {ex}")

    @classmethod
    def limpiar_carrito(cls, db_connection, id_usuario):
        """Elimina todos los productos del carrito del usuario"""
        try:
            with db_connection.cursor() as cursor:
                sql = "DELETE FROM carrito WHERE id_usuario = %s"
                cursor.execute(sql, (id_usuario,))
                db_connection.commit()
                return True
        except Exception as ex:
            db_connection.rollback()
            raise ValueError(f"Error al limpiar carrito: {ex}")