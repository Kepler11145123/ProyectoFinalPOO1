from models.entities.producto import Producto

class CarritoModel:
    @classmethod
    def get_carrito_by_usuario(cls, db_connection, id_usuario):
        """Obtiene todos los items del carrito de un usuario específico"""
        try:
            items_carrito = []
            with db_connection.cursor() as cursor:
                # Agrupar por producto y sumar la cantidad (se almacenan filas por unidad)
                sql = """
                    SELECT p.id, p.nombre, p.precio, p.nombre_columna_imagen, COUNT(c.id_carrito) AS cantidad
                    FROM carrito c
                    JOIN productos p ON c.id_producto = p.id
                    WHERE c.id_usuario = %s
                    GROUP BY p.id, p.nombre, p.precio, p.nombre_columna_imagen
                """
                cursor.execute(sql, (id_usuario,))
                rows = cursor.fetchall()

                for row in rows:
                    items_carrito.append({
                        'id': row[0],  # id_producto
                        'nombre': row[1],
                        'precio': float(row[2]),
                        'imagen': row[3],
                        'cantidad': int(row[4])
                    })
                return items_carrito
        except Exception as ex:
            db_connection.rollback()
            raise ValueError(f"Error al obtener carrito: {ex}")

    @classmethod
    def agregar_producto(cls, db_connection, id_usuario, id_producto, cantidad=1):
        """Agrega una cantidad de producto al carrito del usuario.

        Implementación: la tabla `carrito` guarda una fila por unidad. Antes de insertar validamos
        que la cantidad solicitada no supere el stock disponible menos lo que ya está en el carrito.
        """
        try:
            with db_connection.cursor() as cursor:
                # Obtener stock actual del producto
                cursor.execute("SELECT stock FROM productos WHERE id = %s", (id_producto,))
                prod_row = cursor.fetchone()
                if not prod_row:
                    raise ValueError("Producto no encontrado")
                stock = int(prod_row[0])

                # Cantidad ya en el carrito para este usuario y producto
                cursor.execute("SELECT COUNT(*) FROM carrito WHERE id_usuario = %s AND id_producto = %s", (id_usuario, id_producto))
                in_cart = cursor.fetchone()[0] or 0

                available = stock - int(in_cart)
                if cantidad <= 0:
                    raise ValueError("La cantidad debe ser al menos 1")
                if cantidad > available:
                    raise ValueError(f"Stock insuficiente. Disponibles: {available}")

                # Insertar filas (una por unidad). Usamos executemany para eficiencia.
                values = [(id_usuario, id_producto) for _ in range(cantidad)]
                cursor.executemany("INSERT INTO carrito (id_usuario, id_producto) VALUES (%s, %s)", values)
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