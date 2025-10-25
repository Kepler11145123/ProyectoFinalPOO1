from models.entities.producto import Producto

class ProductoModel:

    @classmethod
    def get_all_products(cls, db_connection):
        productos = []
        try:
            with db_connection.cursor() as cursor:
                cursor.execute("SELECT id, nombre, descripcion, categoria, nombre_columna_imagen, precio, stock FROM productos ORDER BY id ASC")
                rows = cursor.fetchall()

                for row in rows:
                    producto = Producto(
                        id=row[0],
                        nombre=row[1],
                        descripcion=row[2],
                        categoria=row[3],
                        imagen_url=row[4],
                        precio=row[5],
                        stock=row[6]
                    )
                    producto.append(producto)
                # ... (resto de tu lógica para crear la lista de productos)
            return productos
        except Exception as ex:
            # ¡IMPORTANTE! Hacer rollback
            db_connection.rollback()
            raise Exception(f"Error al obtener productos: {ex}")

    @classmethod
    def get_product_by_id(cls, db_connection, producto_id):
        producto = None
        try:
            with db_connection.cursor() as cursor:
                # OJO: Aquí dice 'categoria' pero debería ser 'productos'
                cursor.execute("SELECT id, nombre, descripcion, categoria, nombre_columna_imagen, precio, stock FROM productos WHERE id = %s", (producto_id,))
                row = cursor.fetchone()

                if row:
                    producto = Producto(
                        id=row[0],
                        nombre=row[1],
                        descripcion=row[2],
                        categoria=row[3],
                        imagen_url=row[4],
                        precio=row[5],
                        stock=row[6]
                    )

            return producto
        except Exception as ex:
            # ¡IMPORTANTE! Hacer rollback
            db_connection.rollback()
            raise Exception(f"Error al buscar producto: {ex}")
        
    @classmethod
    def create_product(cls, db_connection, producto_entity):
        try: 
            cursor = db_connection.cursor()
            
            # 1. La consulta SQL para insertar un nuevo registro.
            sql_query = """INSERT INTO productos 
                        (nombre, descripcion, categoria, nombre_columna_imagen, precio, stock) 
                        VALUES (%s, %s, %s, %s, %s, %s)"""
            
            # 2. Los datos que se insertarán, obtenidos desde el objeto 'producto_entity'.
            datos = (
                producto_entity.nombre, 
                producto_entity.descripcion, 
                producto_entity.categoria, 
                producto_entity.imagen_url, 
                producto_entity.precio, 
                producto_entity.stock
            )
            
            # 3. Ejecutamos la consulta con los datos.
            cursor.execute(sql_query, datos)
            
            # 4. Confirmamos y guardamos los cambios en la base de datos. ¡Esto es crucial!
            db_connection.commit()
            
            cursor.close() # Buena práctica cerrar el cursor.
            
            return True # Indicamos que la operación fue un éxito.
            
        except Exception as ex:
            # 5. Si algo falla (ej. un dato incorrecto), revertimos cualquier cambio.
            db_connection.rollback()
            # Y lanzamos la excepción para que app.py pueda mostrar un error.
            raise Exception(f"Error al crear el producto en la base de datos: {ex}")
    
    @classmethod
    def update_product(cls, db_connection, producto_entity):
        """
        Actualiza un producto existente en la base de datos.
        """
        try:
            cursor = db_connection.cursor()
            sql_query = """UPDATE productos 
                           SET nombre = %s, descripcion = %s, categoria = %s, 
                               nombre_columna_imagen = %s, precio = %s, stock = %s 
                           WHERE id = %s"""
            datos = (
                producto_entity.nombre, producto_entity.descripcion, producto_entity.categoria,
                producto_entity.imagen_url, producto_entity.precio, producto_entity.stock,
                producto_entity.id
            )
            cursor.execute(sql_query, datos)
            db_connection.commit()
            cursor.close()
            return True
        except Exception as ex:
            db_connection.rollback()
            raise Exception(f"Error al actualizar producto: {ex}")
        
    @classmethod
    def delete_product(cls, db_connection, producto_id):
        """
        Elimina un producto de la base de datos por su ID.
        """
        try:
            cursor = db_connection.cursor()
            cursor.execute("DELETE FROM productos WHERE id = %s", (producto_id,))
            db_connection.commit()
            cursor.close()
            return True
        except Exception as ex:
            db_connection.rollback()
            raise Exception(f"Error al eliminar producto: {ex}")
            