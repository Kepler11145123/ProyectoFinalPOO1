import re
from flask import Flask, render_template, request, redirect, url_for, session, flash, g
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from flask_wtf.csrf import CSRFProtect
import psycopg2
from psycopg2.extras import DictCursor

from werkzeug.security import generate_password_hash, check_password_hash




app = Flask(__name__)
app.secret_key = '00000'

#Seguridad csrf
csrf = CSRFProtect(app)
#Login manager
login_manager = LoginManager(app)
login_manager.login_view = 'login'

from dotenv import load_dotenv
import os

from models.entities.usuario import Usuario, Cliente, Administrador
from models.UserModel import UserModel
from models.ProductoModel import ProductoModel
from models.entities.producto import Producto

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



@app.route('/')
def inicio():
    # Esta ruta no necesita la base de datos por ahora, pero si la necesitara:
    # conexion = get_db()
    return render_template('inicio.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        try:
            conexion = get_db()
            correo = request.form['correo']
            password = request.form['password']
            
            logged_user = UserModel.login(conexion, correo, password)
            if logged_user:
                login_user(logged_user)
                return redirect(url_for('panel_admin'))
            else:
                flash("Correo o contraseña incorrectos.", "warning")
                return render_template('login.html')
        except Exception as ex:
            app.logger.error(f"Error durante el login: {ex}")
            flash("Ocurrió un error inesperado. Inténtelo más tarde.", "danger")
            return render_template('login.html')
    else:
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
        if current_user.rol != 'admin':
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
def anadir_producto():
    if request.method == 'POST':
        try:
            conexion = get_db()
            # Lógica para añadir el producto...
            # ProductoModel.create_product(conexion, ...)
            flash("Producto añadido exitosamente.", "success")
            return redirect(url_for('panel_admin'))
        except Exception as ex:
            app.logger.error(f"Error al añadir producto: {ex}")
            flash("Error al añadir el producto.", "danger")

    return render_template('formulario_producto.html')


@app.route('/admin/producto/editar/<int:id>', methods=['GET', 'POST'])
@login_required
def editar_producto(id):
    # Obtén la conexión UNA VEZ al principio de la función.
    conexion = get_db() 
    
    if current_user.rol != 'administrador':
        return redirect(url_for('pagina_inicio'))
    
    if request.method == 'POST':
        producto_actualizado = Producto(...)
        try:
            # Ahora 'conexion' sí existe.
            ProductoModel.update_product(conexion, producto_actualizado)
            flash('Producto actualizado correctamente.', 'success')
            return redirect(url_for('panel_admin'))
        except Exception as e:
            flash(f"Error al actualizar: {e}", 'danger')
    
    # Para el método GET, obtenemos el producto y lo mostramos en el formulario
    producto_a_editar = ProductoModel.get_product_by_id(conexion, id)
    return render_template('form_producto.html', accion='Editar', producto=producto_a_editar)

    
@app.route('/admin/producto/eliminar/<int:id>', methods=['POST'])
@login_required

def eliminar_producto(id):
    conexion = get_db()
    if current_user.rol != 'administrador':
        return redirect(url_for('pagina_inicio'))
    
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
        
        # Hashear la contraseña ANTES de pasarla al modelo
        hash_contraseña = generate_password_hash(contraseña)
        
        # Crear la entidad de usuario
        new_user = Usuario(id=None, nombre=nombre, correo=correo, password=hash_contraseña)

        try:
            # Delegar la creación al modelo
            UserModel.create_user(conexion, new_user)
            flash('¡Te has registrado exitosamente! Ahora puedes iniciar sesión.', 'success')
            return redirect(url_for('login'))
        except Exception as e:
            # El modelo lanzará una excepción si el correo ya existe
            flash(str(e), 'danger')
            return render_template('registro.html', nombre=nombre, correo=correo)

    return render_template('registro.html')

@app.route('/inicio')
@login_required
def pagina_inicio():
    return render_template('inicio.html', nombre=current_user.nombre)

@app.route('/catalogo')
@login_required
def catalogo():
    conexion = get_db()
    try:
        productos = ProductoModel.get_all_products(conexion)
        return render_template('catalogo.html', productos=productos, nombre=current_user.nombre)
    except Exception as e:
        flash(f"Error al cargar el catálogo: {str(e)}", 'danger')
        return redirect(url_for('pagina_inicio'))


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

        # Hashear la nueva contraseña
        hash_nueva_contraseña = generate_password_hash(password_new)
        
        # Crear una entidad temporal para la actualización
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


    #cursor = conexion.cursor()
    #cursor.execute("SELECT nombre_columna_imagen FROM categoria WHERE nombre='Luffy'",)
    #if cursor.fetchone():
        #return render_template


if __name__ == '__main__':
    app.run(debug=True)