import re
from flask import Flask, render_template, request, redirect, url_for, session, flash, g
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from flask_wtf.csrf import CSRFProtect
import psycopg2
from psycopg2.extras import DictCursor
from werkzeug.security import generate_password_hash, check_password_hash
from dotenv import load_dotenv
import os
import secrets
from models.entities.usuario import Usuario, Cliente, Administrador
from models.UserModel import UserModel
from models.ProductoModel import ProductoModel
from models.entities.producto import Producto

load_dotenv()
app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY') or secrets.token_hex(32)

csrf = CSRFProtect(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

def get_db():
    if 'db' not in g:
        try:
            # psycopg2 es lo suficientemente inteligente para entender la URL completa.
            DATABASE_URL = os.environ.get('DATABASE_URL')
            g.db = psycopg2.connect(DATABASE_URL)
        except psycopg2.Error as ex:
            # Es buena idea loguear el error para depurar en Render
            app.logger.error(f"FALLO AL CONECTAR A LA BD: {ex}")
            raise Exception(f"Error al conectar con la base de datos: {ex}")
    return g.db

@app.teardown_appcontext
def close_db(e=None):
    """
    Cierra la conexión a la base de datos automáticamente al final de cada petición.
    """
    db = g.pop('db', None)
    if db is not None:
        db.close()
        app.logger.info("Cerrando conexión a la base de datos.")
# VERSIÓN CORREGIDA Y RECOMENDADA
@app.route('/')
def inicio():
    # Si el usuario ya está logueado, llévalo a su panel o al catálogo.
    if current_user.is_authenticated:
        return redirect(url_for('catalogo')) # O 'panel_admin' si lo prefieres
    
    # Si no está logueado, envíalo directamente a la página de login.
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    """Maneja el inicio de sesión de usuarios."""
    
    # ⚠️ IMPORTANTE: Verificar si ya está logueado
    if current_user.is_authenticated:
        if current_user.rol == 'administrador':
            return redirect(url_for('panel_admin'))
        else:
            return redirect(url_for('catalogo'))
    
    if request.method == 'POST':
        try:
            conexion = get_db()
            
            # Obtener datos del formulario
            correo = request.form.get('correo', '').strip()
            contrasena = request.form.get('contraseña', '').strip()
            
            # Validar campos no vacíos
            if not correo or not contrasena:
                flash("Por favor completa todos los campos.", "warning")
                return render_template('login.html')
            
            # ✅ Crear objeto Usuario con paréntesis cerrado
            usuario_temporal = Usuario(
                id=None,
                nombre=None,
                correo=correo,
                password=contrasena
            )  # ← PARÉNTESIS CERRADO
            
            # Intentar login
            logged_user = UserModel.login(conexion, usuario_temporal)
            
            if logged_user:
                # Login exitoso
                login_user(logged_user)
                flash(f"¡Bienvenido, {logged_user.nombre}!", "success")
                
                # Redirigir según rol
                if logged_user.rol == 'administrador':
                    return redirect(url_for('panel_admin'))
                else:
                    return redirect(url_for('catalogo'))
            else:
                # Credenciales incorrectas
                flash("Correo o contraseña incorrectos.", "danger")
                return render_template('login.html')
                
        except Exception as ex:
            app.logger.error(f"Error durante el login: {ex}")
            flash("Error inesperado. Intenta de nuevo.", "danger")
            return render_template('login.html')
    
    # GET: Mostrar formulario
    return render_template('login.html')


@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash("Has cerrado sesión exitosamente.", "success")
    return redirect(url_for('login'))

@login_manager.user_loader
def load_user(user_id):
    """
    Flask-Login usa esta función para recargar el objeto de usuario desde el ID
    almacenado en la sesión. Se ejecuta en cada petición de un usuario logueado.
    """
    try:
        # Obtiene una conexión segura para esta petición específica
        conexion = get_db()
        return UserModel.get_by_id(conexion, user_id)
    except Exception as ex:
        app.logger.error(f"Error en load_user: {ex}")
        return None

@app.route('/panel_admin')
@login_required
def panel_admin():
    try:
        if current_user.rol != 'administrador':
            flash("No tienes permisos para acceder a esta página.", "danger")
            return redirect(url_for('inicio'))
            
        conexion = get_db()
        productos = ProductoModel.get_all_products(conexion)
        return render_template('panel_admin.html', productos=productos)
    except Exception as ex:
        app.logger.error(f"Error en panel_admin: {ex}")
        flash("Error al cargar el panel de administración.", "danger")
        return redirect(url_for('inicio'))

def validar_contraseña(contraseña):
    #!Valida la contraseña con unos parámetros
    errores = []
    if len(contraseña) <8:
        errores.append("Debe tener al menos 8 caracteres.")
    if not re.search(r"[A-Z]", contraseña):
        errores.append("Debe contener al menos una letra mayúscula.")
    if not re.search(r"[0-9]", contraseña):
        errores.append("Debe contener al menos un número")
    if not re.search(r"[\W_]", contraseña):
        errores.append("Debe contener al menos un caracter especial")
    return errores

@app.route('/producto/nuevo', methods=['GET', 'POST'])
@login_required
def nuevo_producto():
    # Verificar permisos de administrador
    if current_user.rol != 'administrador':
        flash("No tienes permisos para añadir productos.", "danger")
        return redirect(url_for('catalogo'))
    
    if request.method == 'POST':
        try:
            # Obtener datos del formulario
            nombre = request.form.get('nombre', '').strip()
            descripcion = request.form.get('descripcion', '').strip()
            categoria = request.form.get('categoria', '').strip()
            nombre_columna_imagen = request.form.get('nombre_columna_imagen', '').strip()
            precio = request.form.get('precio', type=float)
            stock = request.form.get('stock', type=int)
            
            # Validaciones
            errores = []
            if not nombre:
                errores.append("El nombre es obligatorio.")
            if not precio or precio <= 0:
                errores.append("El precio debe ser mayor a 0.")
            if stock is None or stock < 0:
                errores.append("El stock no puede ser negativo.")
            
            if errores:
                for error in errores:
                    flash(error, "danger")
                return render_template('form_producto.html', accion='Añadir')
            
            # Crear objeto Producto
            nuevo_producto = Producto(
                id=None,
                nombre=nombre,
                descripcion=descripcion,
                categoria=categoria,
                nombre_columna_imagen=nombre_columna_imagen,
                precio=precio,
                stock=stock
            )
            # Guardar en base de datos
            conexion = get_db()
            ProductoModel.create_product(conexion, nuevo_producto)
            
            flash("Producto añadido exitosamente.", "success")
            return redirect(url_for('panel_admin'))
            
        except Exception as ex:
            app.logger.error(f"Error al añadir producto: {ex}")
            flash("Error al añadir el producto.", "danger")
            return render_template('form_producto.html', accion='Añadir')
    # GET: Mostrar formulario vacío
    return render_template('form_producto.html', accion='Añadir')

@app.route('/admin/producto/editar/<int:id>', methods=['GET', 'POST'])
@login_required
def editar_producto(id):
    if current_user.rol != 'administrador':
        flash("No tienes permisos para editar productos.", "danger")
        return redirect(url_for('catalogo'))
    
    conexion = get_db()
    if request.method == 'POST':
        try:
            # Obtener datos del formulario
            nombre = request.form.get('nombre', '').strip()
            descripcion = request.form.get('descripcion', '').strip()
            categoria = request.form.get('categoria', '').strip()
            nombre_columna_imagen = request.form.get('nombre_columna_imagen', '').strip()
            precio = request.form.get('precio', type=float)
            stock = request.form.get('stock', type=int)
            
            
            # Validaciones
            if not nombre or not precio or precio <= 0:
                flash("Datos inválidos. Verifica el formulario.", "danger")
                return redirect(url_for('editar_producto', id=id))
            
            # Crear objeto con datos actualizados
            producto_actualizado = Producto(
                id=id,
                nombre=nombre,
                descripcion=descripcion,
                categoria=categoria,
                nombre_columna_imagen=nombre_columna_imagen,
                precio=precio,
                stock=stock
            )
            
            ProductoModel.update_product(conexion, producto_actualizado)
            flash('Producto actualizado correctamente.', 'success')
            return redirect(url_for('panel_admin'))
            
        except Exception as e:
            app.logger.error(f"Error al actualizar: {e}")
            flash("Error al actualizar el producto.", 'danger')
            return redirect(url_for('editar_producto', id=id))
    
    # GET: Obtener producto y mostrar formulario
    producto_a_editar = ProductoModel.get_product_by_id(conexion, id)
    if not producto_a_editar:
        flash("Producto no encontrado.", "warning")
        return redirect(url_for('panel_admin'))
    
    return render_template('form_producto.html', accion='Editar', producto=producto_a_editar)

@app.route('/admin/producto/eliminar/<int:id>', methods=['POST'])
@login_required

def eliminar_producto(id):
    conexion = get_db()
    if current_user.rol != 'administrador':
        return redirect(url_for('inicio'))
    
    try:
        ProductoModel.delete_product(conexion, id)
        flash('Producto eliminado correctamente.', 'success')
    except Exception as e:
        flash(f"Error al eliminar: {e}", 'danger')
    
    return redirect(url_for('panel_admin'))

@app.route('/registro', methods=['GET', 'POST'])
def registro():
    conexion = get_db()
    if request.method == 'POST':
        nombre = request.form['nombre']
        correo = request.form['correo']
        contraseña = request.form['contraseña']
        confirmar_contraseña = request.form['confirmar_contraseña']

        if contraseña != confirmar_contraseña:
            flash('Las contraseñas no coinciden.', 'danger')
            return render_template('registro.html', nombre=nombre, correo=correo)
        
        hash_contraseña = generate_password_hash(contraseña)
        # Crear la entidad de usuario
        new_user = Usuario(id=None, nombre=nombre, correo=correo, password=hash_contraseña)

        try:
            # Delegar la creación al modelo
            UserModel.create_user(conexion, new_user)
            flash('¡Te has registrado exitosamente! Ahora puedes iniciar sesión.', 'success')
            return redirect(url_for('login'))
        except Exception as e:
            flash(str(e), 'danger')
            return render_template('registro.html', nombre=nombre, correo=correo)

    return render_template('registro.html')

@app.route('/inicio')
@login_required
def pagina_inicio():
    return render_template('inicio.html', nombre=current_user.nombre)

@app.route('/catalogo', methods=['GET', 'POST'])
@login_required
def catalogo():
    conexion = get_db()
    
    # Inicializar carrito en la sesión si no existe
    if 'carrito' not in session:
        session['carrito'] = []
    
    # Manejar agregar al carrito
    if request.method == 'POST':
        id_producto = request.form.get('product_id', type=int)
        if id_producto:
            try:
                producto = ProductoModel.get_product_by_id(conexion, id_producto)
                if producto:
                    # Verificar si el producto ya está en el carrito
                    producto_en_carrito = False
                    for item in session['carrito']:
                        if item['id'] == id_producto:
                            item['cantidad'] += 1
                            producto_en_carrito = True
                            break
                    
                    if not producto_en_carrito:
                        # Agregar nuevo producto al carrito
                        session['carrito'].append({
                            'id': producto.id,
                            'nombre': producto.nombre,
                            'precio': float(producto.precio),
                            'imagen': producto.imagen_url,
                            'cantidad': 1
                        })
                    
                    session.modified = True
                    flash(f"{producto.nombre} agregado al carrito", "success")
            except Exception as e:
                flash(f"Error al agregar producto: {str(e)}", 'danger')
    
    try:
        productos = ProductoModel.get_all_products(conexion)
        total_carrito = calcular_total_carrito(session.get('carrito', []))
        return render_template('catalogo.html', productos=productos, nombre=current_user.nombre, total_carrito=total_carrito)
    except Exception as e:
        flash(f"Error al cargar el catálogo: {str(e)}", 'danger')
        return redirect(url_for('inicio'))

@app.route('/carrito')
@login_required
def ver_carrito():
    total_carrito = calcular_total_carrito(session.get('carrito', []))
    return render_template('carrito_compras.html', nombre=current_user.nombre, total_carrito=total_carrito)

@app.route('/carrito/agregar', methods=['POST'])
@login_required
def agregar_al_carrito():
    id_producto = request.form.get('product_id', type=int)
    if not id_producto:
        flash("ID de producto no válido", "danger")
        return redirect(url_for('catalogo'))
    
    try:
        conexion = get_db()
        producto = ProductoModel.get_product_by_id(conexion, id_producto)
        
        if not producto:
            flash("Producto no encontrado", "danger")
            return redirect(url_for('catalogo'))
        
        # Inicializar carrito si no existe
        if 'carrito' not in session:
            session['carrito'] = []
        
        # Verificar si el producto ya está en el carrito
        producto_en_carrito = False
        for item in session['carrito']:
            if item['id'] == id_producto:
                item['cantidad'] += 1
                producto_en_carrito = True
                break
        
        if not producto_en_carrito:
            # Agregar nuevo producto al carrito
            session['carrito'].append({
                'id': producto.id,
                'nombre': producto.nombre,
                'precio': float(producto.precio),
                'imagen': producto.imagen_url,
                'cantidad': 1
            })
        
        session.modified = True
        flash(f"{producto.nombre} agregado al carrito", "success")
        
    except Exception as e:
        flash(f"Error al agregar producto: {str(e)}", 'danger')
    
    return redirect(url_for('catalogo'))

@app.route('/carrito/eliminar/<int:producto_id>', methods=['POST'])
@login_required
def eliminar_del_carrito(producto_id):
    if 'carrito' in session:
        session['carrito'] = [item for item in session['carrito'] if item['id'] != producto_id]
        session.modified = True
        flash("Producto eliminado del carrito", "success")
    
    return redirect(url_for('ver_carrito'))

@app.route('/carrito/limpiar', methods=['POST'])
@login_required
def limpiar_carrito():
    session['carrito'] = []
    session.modified = True
    flash("Carrito limpiado", "success")
    return redirect(url_for('ver_carrito'))

def calcular_total_carrito(carrito):
    """Calcula el total del carrito correctamente"""
    if not carrito:
        return 0
    total = 0
    for item in carrito:
        total += item['precio'] * item['cantidad']
    return total

@app.route('/recuperar', methods=['GET', 'POST'])
def recuperar():
    conexion = get_db()
    if request.method == 'POST':
        correo = request.form['correo']
        password_new = request.form['contraseña']
        confirmar = request.form['confirmar']

        if password_new != confirmar:
            flash('Las contraseñas no coinciden.', 'danger')
            return render_template('recuperar.html', correo=correo)

        hash_nueva_contraseña = generate_password_hash(password_new)
        user_to_update = Usuario(id=None, nombre=None, correo=correo, password=hash_nueva_contraseña)

        try:
            # Delegar la actualización al modelo
            UserModel.update_password(conexion, user_to_update)
            flash('Has cambiado tu contraseña exitosamente. Ahora puedes iniciar sesión.', 'success')
            return redirect(url_for('login'))
        except Exception as e:
            flash(f"Error al recuperar contraseña: {str(e)}", 'danger')
            return render_template('recuperar.html', correo=correo)
            
    return render_template('recuperar.html')



if __name__ == '__main__':
    app.run(debug=True)