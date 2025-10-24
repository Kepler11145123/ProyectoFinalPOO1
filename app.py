import re
from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from flask_wtf.csrf import CSRFProtect
import psycopg2
from psycopg2.extras import DictCursor
from models import Usuario, Cliente, Administrador
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
# conexion = psycopg2.connect(
#     host='localhost',
#     database='commerce',
#     user='postgres',
#     password=''
# )
load_dotenv()
DATABASE_URL = os.environ.get('DATABASE_URL')
conexion = psycopg2.connect(DATABASE_URL)

@app.route('/')
def inicio():
    return render_template('login.html')

@app.route('/login', methods =['POST'])
def login():
    correo = request.form['correo']
    contraseña_formulario = request.form['contraseña']
    cursor = conexion.cursor(cursor_factory=DictCursor)
    cursor.execute("SELECT * FROM usuarios WHERE correo = %s", (correo,))
    datos_usuario = cursor.fetchone()
    cursor.close()

    if datos_usuario:
        if datos_usuario['rol'] == 'administrador':
            usuario = Administrador(datos_usuario['id'], datos_usuario['nombre'], datos_usuario['correo'], datos_usuario['contraseña'], datos_usuario['rol'])
        else: #si no es admin, es cliente
            usuario = Cliente(datos_usuario['id'], datos_usuario['nombre'], datos_usuario['correo'], datos_usuario['contraseña'], datos_usuario['rol'])

        if check_password_hash(usuario.password, contraseña_formulario):
            login_user(usuario)

            if usuario.rol == 'administrador':
                return redirect(url_for('panel_admin'))
            else: 
                return redirect(url_for('pagina_inicio'))
        else:
            flash('Contraseña incorrecta.', 'danger')
            return redirect(url_for('login'))
    else:
        flash('Usuario no encontrado.', 'danger')
        return redirect(url_for('login'))

@login_manager.user_loader
def load_user(user_id):
    # Usa DictCursor para acceder a los datos por nombre, es más seguro.
    cursor = conexion.cursor(cursor_factory=DictCursor)
    cursor.execute("SELECT * FROM usuarios WHERE id = %s", (user_id,))
    datos_usuario = cursor.fetchone()
    cursor.close()

    if datos_usuario:
        # Revisa el rol y crea el objeto correcto.
        if datos_usuario['rol'] == 'administrador':
            return Administrador(
                id=datos_usuario['id'],
                nombre=datos_usuario['nombre'],
                correo=datos_usuario['correo'],
                password=datos_usuario['contraseña'],
                rol=datos_usuario['rol']
            )
        else:
            return Cliente(
                id=datos_usuario['id'],
                nombre=datos_usuario['nombre'],
                correo=datos_usuario['correo'],
                password=datos_usuario['contraseña'],
                rol=datos_usuario['rol']
            )
    return None

@app.route('/panel_admin')
@login_required
def panel_admin():
    if current_user.rol != 'administrador':
        flash('Acceso no autorizado.', 'danger')
        return redirect(url_for('pagina_inicio'))
    
    cursor = conexion.cursor(cursor_factory=DictCursor)
    cursor.execute("SELECT * FROM categoria ORDER BY id ASC")
    productos = cursor.fetchall()
    cursor.close()

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
        nombre = request.form['nombre']
        descripcion = request.form['descripcion']
        categoria = request.form['categoria']
        imagen_url = request.form['imagen_url']
        precio = request.form['precio']
        stock = request.form['stock']

        cursor = conexion.cursor()
        cursor.execute(
            "INSERT INTO categoria (nombre, descripcion, categoria, nombre_columna_imagen, precio, stock) VALUES (%s, %s, %s, %s, %s, %s)",
            (nombre, descripcion, categoria, imagen_url, precio, stock)
        )
        conexion.commit()
        flash('Producto añadido correctamente', 'sucess')
        return redirect(url_for('panel_admin'))
    
    return render_template('form_producto.html', accion = 'Crear', producto=None)

@app.route('/admin/producto/editar/<int:id>', methods=['GET', 'POST'])
@login_required
def editar_producto(id):
    if current_user.rol != 'administrador':
        return redirect(url_for('pagina_inicio'))
    
    cursor = conexion.cursor(cursor_factory=DictCursor)
    if request.method == 'POST':
        nombre = request.form['nombre']
        descripcion = request.form['descripcion']
        categoria = request.form['categoria']
        imagen_url = request.form['imagen_url']
        precio = request.form['precio']
        stock = request.form['stock']

        cursor.execute (
            "UPDATE categoria SET nombre = %s, descripcion = %s, categoria = %s, nombre_columna_imagen = %s, precio = %s, stock =%s WHERE id = %s",
            (nombre, descripcion, categoria, imagen_url, precio, stock, id)
        )
        conexion.commit()
        cursor.close()
        flash('Producto actualizado correctamente', 'sucess')
        return redirect(url_for('panel_admin'))
    
    cursor.execute("SELECT * FROM categoria WHERE id =%s", (id,))
    producto = cursor.fetchone()
    cursor.close()
    return render_template('form_producto.html', accion='Editar', producto=producto)
    
@app.route('/admin/producto/eliminar/<int:id>', methods=['POST'])
@login_required
def eliminar_producto(id):
    if current_user.rol != 'administrador':
        return redirect(url_for('pagina_inicio'))
    
    cursor = conexion.cursor()
    cursor.execute("DELETE FROM categoria WHERE id = %s", (id,))
    conexion.commit()
    flash('Elemento eliminado correctamente', 'danger')
    return redirect(url_for('panel_admin'))
        


@app.route('/registro', methods=['GET','POST'])
def registro():
    if request.method == 'POST':
        nombre = request.form['nombre']
        correo = request.form['correo']
        contraseña = request.form['contraseña']
        #*Confirmar contraseña
        confirmar_contraseña = request.form['confirmar_contraseña']
        #Verificar si coinciden, si no coinciden recarga la página pero sin perder la información ingresada
        if contraseña != confirmar_contraseña:
            return render_template('registro.html',
                                   mensaje_error="Las contraseñas no coinciden.",
                                   nombre = nombre,
                                   correo = correo)
        errores_pass = validar_contraseña(contraseña)
        if errores_pass:
        #Si hay errores se recarga y muestra el error
            return render_template('registro.html', 
                                   mensaje_error_pass=errores_pass,
                                   nombre=nombre, 
                                   correo=correo)
        #Verificar correo duplicado
        cursor = conexion.cursor()
        cursor.execute("SELECT * FROM usuarios WHERE correo=%s", (correo,))
        if cursor.fetchone():
            return render_template('registro.html',
                                   mensaje_error="El correo ya está registrado.",
                                   nombre = nombre,
                                   correo = correo)
        
        hash_contraseña = generate_password_hash(contraseña)   
        cursor.execute("INSERT INTO usuarios (nombre, correo, contraseña) VALUES (%s, %s, %s)", 
                   (nombre, correo, hash_contraseña))
        conexion.commit()
        
        flash('Te has registrado exitosamente! Ahora puedes iniciar sesión.','success')
        return redirect('/')

    return render_template('registro.html')

@app.route('/inicio')
@login_required
def pagina_inicio():
    return render_template('inicio.html', nombre=current_user.nombre)

@app.route('/catalogo')
@login_required
def catalogo():
    try:
        cursor = conexion.cursor(cursor_factory=DictCursor)

        cursor.execute("SELECT id, nombre, nombre_columna_imagen, descripcion, categoria FROM categoria")

        productos = cursor.fetchall()
        cursor.close()
        return render_template('catalogo.html', productos = productos, nombre=current_user.nombre)

    except Exception as e:
        print(f"Error al consultar el catálogo: {e}")
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
        passwordnew = request.form['contraseña']
        confirmar = request.form['confirmar']

        cursor = conexion.cursor()
        cursor.execute("SELECT * FROM usuarios WHERE correo=%s", (correo,))
        usuario = cursor.fetchone()

        if passwordnew != confirmar:
            return render_template('recuperar.html',
                                   mensaje_error="Las contraseñas no coinciden.",
                                   correo = correo,)
        
        errores_pass = validar_contraseña(passwordnew)
        if errores_pass:
            return render_template('recuperar.html',
                                   mensaje_error="Las contraseñas no coinciden.",
                                   correo = correo)

        hash_nueva_contraseña = generate_password_hash(passwordnew)
        cursor.execute("UPDATE usuarios SET contraseña = %s WHERE correo = %s", (hash_nueva_contraseña, correo))
        conexion.commit()

        flash('Has cambiado tu contraseña exitosamente, ahora puedes iniciar sesión.','success')
        return redirect('/')
    return render_template('recuperar.html')


    #cursor = conexion.cursor()
    #cursor.execute("SELECT nombre_columna_imagen FROM categoria WHERE nombre='Luffy'",)
    #if cursor.fetchone():
        #return render_template


if __name__ == '__main__':
    app.run(debug=True)