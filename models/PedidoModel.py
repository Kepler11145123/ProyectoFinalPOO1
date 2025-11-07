from models.entities.pedido import Pedido, DetallePedido
from datetime import datetime

class PedidoModel:
    @classmethod
    def crear_pedido(cls, conexion, id_cliente, total, items_carrito):
        """Crea un nuevo pedido en la tabla `pedidos` y sus detalles en `detalle_pedidos`.
        Firma: crear_pedido(conexion, id_cliente, total, items_carrito)
        """
        try:
            cursor = conexion.cursor()

            # Insertar cabecera del pedido
            cursor.execute("""
                INSERT INTO pedidos (id_cliente, data_pedido, status)
                VALUES (%s, %s, %s)
                RETURNING id_pedido
            """, (id_cliente, datetime.now(), 'completado'))

            id_pedido = cursor.fetchone()[0]

            # Insertar detalles en detalle_pedidos
            for item in items_carrito:
                # item debería ser un dict con keys id, cantidad
                id_producto = item.get('id') if isinstance(item, dict) else getattr(item, 'id', None)
                cantidad = item.get('cantidad') if isinstance(item, dict) else getattr(item, 'cantidad', 1)

                cursor.execute("""
                    INSERT INTO detalle_pedidos (id_pedido, id_producto, cantidad)
                    VALUES (%s, %s, %s)
                """, (id_pedido, id_producto, int(cantidad)))

            conexion.commit()
            cursor.close()
            return id_pedido
        except Exception as ex:
            conexion.rollback()
            raise Exception(f"Error al crear el pedido: {ex}")

    @classmethod
    def obtener_todos_pedidos(cls, conexion):
        """Obtiene todos los pedidos con su total calculado a partir de productos."""
        try:
            cursor = conexion.cursor()
            cursor.execute("""
                SELECT 
                    p.id_pedido,
                    p.id_cliente,
                    u.nombre,
                    u.correo,
                    p.data_pedido,
                    p.status,
                    COALESCE(SUM(dp.cantidad * pr.precio), 0) as total
                FROM pedidos p
                JOIN usuarios u ON p.id_cliente = u.id
                LEFT JOIN detalle_pedidos dp ON p.id_pedido = dp.id_pedido
                LEFT JOIN productos pr ON dp.id_producto = pr.id
                GROUP BY p.id_pedido, p.id_cliente, u.nombre, u.correo, p.data_pedido, p.status
                ORDER BY p.data_pedido DESC
            """)

            pedidos = []
            for row in cursor.fetchall():
                pedidos.append({
                    'id_pedido': row[0],
                    'id_cliente': row[1],
                    'nombre_cliente': row[2],
                    'correo_cliente': row[3],
                    'data_pedido': row[4],
                    'status': row[5],
                    'total': float(row[6])
                })

            cursor.close()
            return pedidos
        except Exception as ex:
            raise Exception(f"Error al obtener los pedidos: {ex}")

    @classmethod
    def obtener_detalles_pedido(cls, conexion, id_pedido):
        """Obtiene los detalles de un pedido específico"""
        try:
            cursor = conexion.cursor()
            cursor.execute("""
                SELECT 
                    dp.id_detalle,
                    dp.id_pedido,
                    dp.id_producto,
                    dp.cantidad,
                    pr.precio as precio_unitario,
                    (dp.cantidad * pr.precio) as subtotal,
                    pr.nombre as nombre_producto
                FROM detalle_pedidos dp
                JOIN productos pr ON dp.id_producto = pr.id
                WHERE dp.id_pedido = %s
            """, (id_pedido,))

            detalles = []
            for row in cursor.fetchall():
                detalles.append({
                    'id_detalle': row[0],
                    'id_pedido': row[1],
                    'id_producto': row[2],
                    'cantidad': row[3],
                    'precio_unitario': float(row[4]),
                    'subtotal': float(row[5]),
                    'nombre_producto': row[6]
                })

            cursor.close()
            return detalles
        except Exception as ex:
            raise Exception(f"Error al obtener los detalles del pedido: {ex}")

    # Compatibilidad: nombre singular usado en app.py
    @classmethod
    def obtener_detalle_pedido(cls, conexion, id_pedido):
        return cls.obtener_detalles_pedido(conexion, id_pedido)

    @classmethod
    def obtener_pedido_por_id(cls, conexion, id_pedido):
        """Obtiene informacion de un pedido en especial"""
        try:
            cursor = conexion.cursor()
            cursor.execute("""
                SELECT 
                    p.id_pedido,
                    p.id_cliente,
                    u.nombre,
                    u.correo,
                    p.data_pedido,
                    p.status,
                    COALESCE(SUM(dp.cantidad * pr.precio), 0) as total
                FROM pedidos p
                JOIN usuarios u ON p.id_cliente = u.id
                LEFT JOIN detalle_pedidos dp ON p.id_pedido = dp.id_pedido
                LEFT JOIN productos pr ON dp.id_producto = pr.id
                WHERE p.id_pedido = %s
                GROUP BY p.id_pedido, p.id_cliente, u.nombre, u.correo, p.data_pedido, p.status
            """, (id_pedido,))

            row = cursor.fetchone()
            cursor.close()

            if not row:
                return None

            return {
                'id_pedido': row[0],
                'id_cliente': row[1],
                'nombre_cliente': row[2],
                'correo_cliente': row[3],
                'data_pedido': row[4],
                'status': row[5],
                'total': float(row[6])
            }
        except Exception as ex:
            raise Exception(f"Error al obtener el pedido por ID: {ex}")

    @classmethod
    def actualizar_detalle(cls, conexion, id_detalle, id_producto, cantidad):
        """Actualiza un detalle existente (producto y cantidad)."""
        try:
            cursor = conexion.cursor()
            cursor.execute("""
                UPDATE detalle_pedidos SET id_producto = %s, cantidad = %s WHERE id_detalle = %s
            """, (id_producto, int(cantidad), id_detalle))
            conexion.commit()
            cursor.close()
            return True
        except Exception as ex:
            conexion.rollback()
            raise Exception(f"Error al actualizar detalle: {ex}")

    @classmethod
    def agregar_detalle(cls, conexion, id_pedido, id_producto, cantidad):
        """Agrega una nueva fila en detalle_pedidos para un pedido existente."""
        try:
            cursor = conexion.cursor()
            cursor.execute("""
                INSERT INTO detalle_pedidos (id_pedido, id_producto, cantidad)
                VALUES (%s, %s, %s)
                RETURNING id_detalle
            """, (id_pedido, id_producto, int(cantidad)))
            id_detalle = cursor.fetchone()[0]
            conexion.commit()
            cursor.close()
            return id_detalle
        except Exception as ex:
            conexion.rollback()
            raise Exception(f"Error al agregar detalle: {ex}")

    @classmethod
    def eliminar_detalle(cls, conexion, id_detalle):
        """Elimina un detalle por su id."""
        try:
            cursor = conexion.cursor()
            cursor.execute("DELETE FROM detalle_pedidos WHERE id_detalle = %s", (id_detalle,))
            conexion.commit()
            cursor.close()
            return True
        except Exception as ex:
            conexion.rollback()
            raise Exception(f"Error al eliminar detalle: {ex}")