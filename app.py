import re
from flask import Flask, render_template, request, redirect, url_for, session, flash
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
login_manager.login_view = 'inicio'

from dotenv import load_dotenv
import os

from models.entities.usuario import Usuario, Cliente, Administrador
from models.UserModel import UserModel
from models.ProductoModel import ProductoModel
from models.entities.producto import Producto

load_dotenv()
DATABASE_URL = os.environ.get('DATABASE_URL')
conexion = psycopg2.connect(DATABASE_URL)

@app.route('/', methods=['GET', 'POST'])
def inicio():
    if request.method == 'POST':
        # Crear la entidad de usuario con los datos del formulario
        user_entity = Usuario(None, None, request.form['correo'], request.form['contraseña'])
        
        # El modelo se encarga de la lógica de autenticación
        logged_user = UserModel.login(conexion, user_entity)
        
        if logged_user:
            login_user(logged_user)
            if logged_user.rol == 'administrador':
                return redirect(url_for('panel_admin'))
            else:
                return redirect(url_for('pagina_inicio')) # Asumiendo que esta es tu página principal para clientes
        else:
            flash('Correo o contraseña incorrectos.', 'danger')
            # Si falla el login, volvemos a mostrar la misma página de login
            return render_template('login.html') 
            
    # Para el método GET
    if current_user.is_authenticated:
        # Si ya está logueado, lo mandamos a su página correspondiente
        if current_user.rol == 'administrador':
            return redirect(url_for('panel_admin'))
        else:
            return redirect(url_for('pagina_inicio'))
    
    # Si no está logueado y es GET, simplemente mostramos la página de login
    return render_template('login.html')

# Puedes eliminar la ruta @app.route('/login') separada si la tenías, 
# ya que ahora está integrada en la ruta raíz.



@login_manager.user_loader
def load_user(user_id):
    # El modelo se encarga de buscar al usuario por su ID
    return UserModel.get_by_id(conexion, user_id)

@app.route('/panel_admin')
@login_required
def panel_admin():
    if current_user.rol != 'administrador':
        return redirect(url_for('pagina_inicio'))
    
    productos = ProductoModel.get_all_products(conexion)
    return render_template('panel_admin.html', productos=productos)

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

@app.route('/admin/productos/nuevo', methods=['GET', 'POST'])
@login_required
def nuevo_producto():
    if current_user.rol != 'administrador':
        return redirect(url_for('pagina_inicio'))
    
    if request.method == 'POST':
        nuevo = Producto(
            id=None, nombre=request.form['nombre'], descripcion=request.form['descripcion'],
            categoria=request.form['categoria'], imagen_url=request.form['imagen_url'],
            precio=request.form['precio'], stock=request.form['stock']
        )
        try:
            ProductoModel.create_product(conexion, nuevo)
            flash('Producto añadido correctamente.', 'success')
            return redirect(url_for('panel_admin'))
        except Exception as e:
            flash(f"Error al crear el producto: {e}", 'danger')

    return render_template('form_producto.html', accion='Crear', producto=None)

@app.route('/admin/producto/editar/<int:id>', methods=['GET', 'POST'])
@login_required
def editar_producto(id):
    if current_user.rol != 'administrador':
        return redirect(url_for('pagina_inicio'))
    
    if request.method == 'POST':
        producto_actualizado = Producto(
            id=id, nombre=request.form['nombre'], descripcion=request.form['descripcion'],
            categoria=request.form['categoria'], imagen_url=request.form['imagen_url'],
            precio=request.form['precio'], stock=request.form['stock']
        )
        try:
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
    try:
        productos = ProductoModel.get_all_products(conexion)
        return render_template('catalogo.html', productos=productos, nombre=current_user.nombre)
    except Exception as e:
        flash(f"Error al cargar el catálogo: {str(e)}", 'danger')
        return redirect(url_for('pagina_inicio'))

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect('/')

@app.route('/recuperar', methods=['GET', 'POST'])
def recuperar():
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