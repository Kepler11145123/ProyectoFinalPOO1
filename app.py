import re
from flask import Flask, render_template, request, redirect, url_for, session, flash, g, get_flashed_messages, jsonify
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
from models.CarritoModel import CarritoModel
from models.entities.producto import Producto
from reportlab.pdfgen import canvas
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.platypus import Table, TableStyle
from datetime import datetime
LOGIN_TEMPLATE = 'login.html'
FORM_PRODUCTO_TEMPLATE = 'form_producto.html'
REGISTRO_TEMPLATE = 'registro.html'
RECUPERAR_TEMPLATE = 'recuperar.html'
ACTION_AÑADIR = 'Añadir'
FORM_CONTRASEÑA = 'contraseña'
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
            raise ValueError(f"Error al conectar con la base de datos: {ex}")
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
    if current_user.is_authenticated:
        return _redirect_authenticated_user()
    
    if request.method == 'POST':
        return _handle_login_attempt()
    
    return render_template(LOGIN_TEMPLATE)

        #Funciones auxiliares 

def _redirect_authenticated_user():
    if current_user.rol == 'administrador':
        return redirect(url_for('panel_admin'))
    return redirect(url_for('catalogo'))

def _handle_login_attempt():
    try:
        correo, contrasena = _get_login_credentials()

        if not _are_credentials_valid(correo, contrasena):
            flash("Por favor completa todos los campos.", "warning")
            return render_template(LOGIN_TEMPLATE)
        
        logged_user = _authenticated_user(correo, contrasena)

        if not logged_user:
            flash("Correo o contraseña incorrectos.", "danger")
            return render_template(LOGIN_TEMPLATE)
        #Login exitoso
        login_user(logged_user)
        flash(f"Bienvenido, {logged_user.nombre}!", "success")
        return _redirect_authenticated_user()

    except Exception as ex:
        app.logger.error(f"Error durante el login:{ex}")
        flash("Error inesperado. Intenta de nuevo.","danger")
        return render_template(LOGIN_TEMPLATE)
    
def _get_login_credentials():
    correo = request.form.get('correo','').strip()
    contrasena = request.form.get(FORM_CONTRASEÑA,'').strip()
    return correo, contrasena

def _are_credentials_valid(correo, contrasena):
    return bool(correo and contrasena)

def _authenticated_user(correo, contrasena):
    conexion = get_db()
    usuario_temporal = Usuario(
        id=None,
        nombre=None,
        correo=correo,
        password=contrasena
    )

    return UserModel.login(conexion, usuario_temporal)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    get_flashed_messages()
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

def validar_contrasena(contrasena):
    #!Valida la contraseña con unos parámetros
    errores = []
    if len(contrasena) <8:
        errores.append("Debe tener al menos 8 caracteres.")
    if not re.search(r"[A-Z]", contrasena):
        errores.append("Debe contener al menos una letra mayúscula.")
    if not re.search(r"[\d]", contrasena):
        errores.append("Debe contener al menos un número")
    if not re.search(r"[\W]", contrasena):
        errores.append("Debe contener al menos un caracter especial")
    return errores

@app.route('/producto/nuevo', methods=['GET', 'POST'])
@login_required
def nuevo_producto():
    # Verificar permisos de administrador
    if current_user.rol != 'administrador':
        flash("No tienes permisos para añadir productos.", "danger")
        return redirect(url_for('catalogo'))
    
    if request.method == 'GET':
        return render_template(FORM_PRODUCTO_TEMPLATE, accion=ACTION_AÑADIR)
    
    # POST: Procesar formulario
    return _handle_create_product()

def _handle_create_product():
        try:
            form_data = _get_product_form_data()

            errores = _validate_product_data(form_data)
            if errores:
                for error in errores:
                    flash(error, "danger")
                return render_template(FORM_PRODUCTO_TEMPLATE, accion = ACTION_AÑADIR)
            
            _create_and_save_product(form_data)

            flash("Producto añadido correctamente. ", "sucess")
            return redirect(url_for('panel_admin'))
        
        except Exception as ex:
            app.logger.error(f"Error al añadir producto: {ex}")
            flash("Error al añadir el producto.", "danger")
            return render_template(FORM_PRODUCTO_TEMPLATE, accion=ACTION_AÑADIR)

def _get_product_form_data():
    return {
        'nombre': request.form.get('nombre','').strip(),
        'descripcion': request.form.get('descripcion','').strip(),
        'categoria': request.form.get('categoria','').strip(),
        'nombre_columna_imagen': request.form.get('nombre_columna_imagen','').strip(),
        'precio': request.form.get('precio',type=float),
        'stock': request.form.get('stock',type=int)
    }

def _validate_product_data(form_data):
    errores = []
    if not _is_product_name_valid(form_data['nombre']):
        errores.append("El nombre es obligatorio.")
    
    if not _is_product_price_valid(form_data['precio']):
        errores.append("El precio debe ser mayor a 0.")
    
    if not _is_product_stock_valid(form_data['stock']):
        errores.append("El stock no puede ser negativo.")

    return errores

def _is_product_name_valid(nombre):
    return bool(nombre)

def _is_product_price_valid(precio):
    return precio is not None and precio > 0

def _is_product_stock_valid(stock):
    return stock is not None and stock >= 0

def _create_and_save_product(form_data):
    nuevo_producto = Producto (
        id=None,
        nombre=form_data['nombre'],
        descripcion=form_data['descripcion'],
        categoria=form_data['categoria'],
        nombre_columna_imagen=form_data['nombre_columna_imagen'],
        precio=form_data['precio'],
        stock=form_data['stock']
    )
    conexion = get_db()
    ProductoModel.create_product(conexion, nuevo_producto)


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
        contrasena = request.form[FORM_CONTRASEÑA]
        confirmar_contrasena = request.form['confirmar_contraseña']

        if contrasena != confirmar_contrasena:
            flash('Las contraseñas no coinciden.', 'danger')
            return render_template(REGISTRO_TEMPLATE, nombre=nombre, correo=correo)
        
        hash_contrasena = generate_password_hash(contrasena)
        # Crear la entidad de usuario
        new_user = Usuario(id=None, nombre=nombre, correo=correo, password=hash_contrasena)

        try:
            # Delegar la creación al modelo
            UserModel.create_user(conexion, new_user)
            flash('¡Te has registrado exitosamente! Ahora puedes iniciar sesión.', 'success')
            return redirect(url_for('login'))
        except Exception as e:
            flash(str(e), 'danger')
            return render_template(REGISTRO_TEMPLATE, nombre=nombre, correo=correo)

    return render_template(REGISTRO_TEMPLATE)

@app.route('/inicio')
@login_required
def pagina_inicio():
    return render_template('inicio.html', nombre=current_user.nombre)

@app.route('/catalogo', methods=['GET', 'POST'])
@login_required
def catalogo():
    conexion = get_db()
    
    # Manejar agregar al carrito
    if request.method == 'POST':
        id_producto = request.form.get('product_id', type=int)
        if id_producto:
            try:
                # Agregar el producto al carrito en la base de datos
                CarritoModel.agregar_producto(conexion, current_user.id, id_producto)
                producto = ProductoModel.get_product_by_id(conexion, id_producto)
                flash(f"{producto.nombre} agregado al carrito", "success")
            except Exception as e:
                flash(f"Error al agregar producto: {str(e)}", 'danger')
    
    try:
        productos = ProductoModel.get_all_products(conexion)
        # Obtener el carrito del usuario desde la base de datos
        items_carrito = CarritoModel.get_carrito_by_usuario(conexion, current_user.id)
        total_carrito = calcular_total_carrito(items_carrito)
        return render_template('catalogo.html', 
                            productos=productos, 
                            nombre=current_user.nombre, 
                            total_carrito=total_carrito, 
                            carrito=items_carrito)
    except Exception as e:
        flash(f"Error al cargar el catálogo: {str(e)}", 'danger')
        return redirect(url_for('inicio'))


@app.route('/api/carrito/agregar', methods=['POST'])
@login_required
def api_agregar_carrito():
    """API para agregar un producto al carrito y devolver el estado actualizado en JSON."""
    try:
        data = request.get_json(force=True, silent=True) or request.form
        id_producto = None
        if isinstance(data, dict):
            id_producto = data.get('product_id')
        else:
            id_producto = request.form.get('product_id')

        if not id_producto:
            return jsonify({'success': False, 'message': 'ID de producto no enviado'}), 400

        id_producto = int(id_producto)
        conexion = get_db()
        CarritoModel.agregar_producto(conexion, current_user.id, id_producto)

        # Obtener carrito actualizado
        items_carrito = CarritoModel.get_carrito_by_usuario(conexion, current_user.id)
        total = calcular_total_carrito(items_carrito)

        return jsonify({
            'success': True,
            'message': 'Producto agregado al carrito',
            'items': items_carrito,
            'count': len(items_carrito),
            'total': total
        })
    except Exception as ex:
        app.logger.error(f"Error en API agregar carrito: {ex}")
        return jsonify({'success': False, 'message': str(ex)}), 500


@app.route('/api/carrito/eliminar', methods=['POST'])
@login_required
def api_eliminar_carrito():
    """API para eliminar un producto del carrito y devolver estado actualizado en JSON."""
    try:
        data = request.get_json(force=True, silent=True) or request.form
        id_producto = None
        if isinstance(data, dict):
            id_producto = data.get('product_id')
        else:
            id_producto = request.form.get('product_id')

        if not id_producto:
            return jsonify({'success': False, 'message': 'ID de producto no enviado'}), 400

        id_producto = int(id_producto)
        conexion = get_db()
        CarritoModel.eliminar_producto(conexion, current_user.id, id_producto)

        items_carrito = CarritoModel.get_carrito_by_usuario(conexion, current_user.id)
        total = calcular_total_carrito(items_carrito)

        return jsonify({
            'success': True,
            'message': 'Producto eliminado del carrito',
            'items': items_carrito,
            'count': len(items_carrito),
            'total': total
        })
    except Exception as ex:
        app.logger.error(f"Error en API eliminar carrito: {ex}")
        return jsonify({'success': False, 'message': str(ex)}), 500


@app.route('/api/carrito/limpiar', methods=['POST'])
@login_required
def api_limpiar_carrito():
    """API para limpiar el carrito del usuario y devolver estado actualizado en JSON."""
    try:
        conexion = get_db()
        CarritoModel.limpiar_carrito(conexion, current_user.id)

        items_carrito = CarritoModel.get_carrito_by_usuario(conexion, current_user.id)
        total = calcular_total_carrito(items_carrito)

        return jsonify({
            'success': True,
            'message': 'Carrito limpiado',
            'items': items_carrito,
            'count': len(items_carrito),
            'total': total
        })
    except Exception as ex:
        app.logger.error(f"Error en API limpiar carrito: {ex}")
        return jsonify({'success': False, 'message': str(ex)}), 500

@app.route('/carrito')
@login_required
def ver_carrito():
    try:
        conexion = get_db()
        items_carrito = CarritoModel.get_carrito_by_usuario(conexion, current_user.id)
        total_carrito = calcular_total_carrito(items_carrito)
        return render_template('carrito_compras.html', 
                            nombre=current_user.nombre, 
                            carrito=items_carrito, 
                            total_carrito=total_carrito)
    except Exception as e:
        flash(f"Error al cargar el carrito: {str(e)}", 'danger')
        return redirect(url_for('catalogo'))

@app.route('/carrito/eliminar/<int:producto_id>', methods=['POST'])
@login_required
def eliminar_del_carrito(producto_id):
    try:
        conexion = get_db()
        CarritoModel.eliminar_producto(conexion, current_user.id, producto_id)
        flash("Producto eliminado del carrito", "success")
    except Exception as e:
        flash(f"Error al eliminar producto: {str(e)}", 'danger')
    
    return redirect(url_for('ver_carrito'))


@app.route('/generar_recibo', methods=['POST'])
@login_required
def generar_recibo():
    # Usamos la función auxiliar para mantener la lógica reutilizable.
    try:
        conexion = get_db()
        items_carrito = CarritoModel.get_carrito_by_usuario(conexion, current_user.id)
        if not items_carrito:
            flash("No hay items en el carrito", "warning")
            return redirect(url_for('ver_carrito'))

        pdf_filename = _generate_pdf_for_items(items_carrito, current_user)

        # Limpiar carrito
        CarritoModel.limpiar_carrito(conexion, current_user.id)

        return redirect(url_for('static', filename=f'recibos/{pdf_filename}'))
    except Exception as e:
        app.logger.error(f"Error generando recibo: {e}")
        flash("Error al generar el recibo", "danger")
        return redirect(url_for('ver_carrito'))


def _normalize_item(item):
    """Normaliza un item retornando dict con claves: id, nombre, precio, cantidad."""
    if isinstance(item, dict):
        return {
            'id': item.get('id') or item.get('producto_id') or item.get('product_id'),
            'nombre': item.get('nombre') or item.get('titulo') or item.get('name') or '',
            'precio': float(item.get('precio') or item.get('price') or 0),
            'cantidad': int(item.get('cantidad') or item.get('qty') or item.get('quantity') or 1)
        }

    # Intentar atributos del objeto
    try:
        pid = getattr(item, 'id', None) or getattr(item, 'producto_id', None) or getattr(item, 'product_id', None)
        nombre = getattr(item, 'nombre', None) or getattr(item, 'titulo', None) or getattr(item, 'name', None) or ''
        precio = getattr(item, 'precio', None) or getattr(item, 'price', None) or 0
        cantidad = getattr(item, 'cantidad', None) or getattr(item, 'qty', None) or getattr(item, 'quantity', None) or 1
        return {'id': pid, 'nombre': nombre, 'precio': float(precio), 'cantidad': int(cantidad)}
    except Exception:
        # Fallback: intentar como secuencia (tupla/lista)
        try:
            pid = item[0]; nombre = item[1]; precio = float(item[2]); cantidad = int(item[3])
            return {'id': pid, 'nombre': nombre, 'precio': precio, 'cantidad': cantidad}
        except Exception:
            return {'id': None, 'nombre': str(item), 'precio': 0.0, 'cantidad': 1}


def _aggregate_items(items_carrito):
    """Agrupa items por id y suma cantidades. Devuelve dict de agregados."""
    agregados = {}
    if not items_carrito:
        return agregados

    for item in items_carrito:
        it = _normalize_item(item)
        pid = it['id']
        precio = float(it['precio'])
        cantidad = int(it['cantidad'])
        nombre = it['nombre']

        if pid in agregados:
            agregados[pid]['cantidad'] += cantidad
            agregados[pid]['precio'] = precio  # conservar último precio conocido
        else:
            agregados[pid] = {'id': pid, 'nombre': nombre, 'precio': precio, 'cantidad': cantidad}

    return agregados


def _generate_pdf_for_items(items_carrito, usuario):
    """Genera el PDF a partir de una lista de items (diccionarios) y retorna el nombre de archivo generado."""
    # Crear directorio para recibos si no existe
    recibos_dir = os.path.join(app.root_path, 'static', 'recibos')
    os.makedirs(recibos_dir, exist_ok=True)

    # Nombre único para el PDF
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    pdf_filename = f"recibo_{getattr(usuario, 'id', 'anon')}_{timestamp}.pdf"
    pdf_path = os.path.join(recibos_dir, pdf_filename)

    # Crear PDF
    c = canvas.Canvas(pdf_path, pagesize=letter)
    width, height = letter

    # Encabezado
    c.setFont("Helvetica-Bold", 18)
    c.drawString(50, height - 50, "Recibo de Compra")

    # Información del cliente y fecha
    c.setFont("Helvetica", 11)
    c.drawString(50, height - 80, f"Cliente: {getattr(usuario, 'nombre', '')}")
    correo = getattr(usuario, 'correo', '') if hasattr(usuario, 'correo') else ''
    c.drawString(50, height - 100, f"Correo: {correo}")
    fecha_str = datetime.now().strftime('%d/%m/%Y %H:%M:%S')
    c.drawString(50, height - 120, f"Fecha: {fecha_str}")

    # Agrupar productos por ID y sumar cantidades (delegado a helper para reducir complejidad)
    agregados = _aggregate_items(items_carrito)

    # Preparar datos de la tabla
    data = [["Producto", "Cantidad", "Precio Unit.", "Subtotal"]]
    total = 0.0
    for agg in agregados.values():
        precio = float(agg.get('precio', 0))
        cantidad = int(agg.get('cantidad', 0))
        subtotal = precio * cantidad
        total += subtotal
        data.append([
            agg.get('nombre', ''),
            str(cantidad),
            f"${precio:.2f}",
            f"${subtotal:.2f}"
        ])

    # Fila de total
    data.append(["", "", "Total:", f"${total:.2f}"])

    # Crear tabla
    table = Table(data, colWidths=[240, 80, 100, 100])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#4a5568')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (1, 1), (-1, -2), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 11),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor('#f7fafc')),
        ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold')
    ]))

    # Dibujar tabla
    table_width, table_height = table.wrap(0, 0)
    y_position = height - 160 - table_height
    if y_position < 80:
        y_position = 80

    table.wrapOn(c, width, height)
    table.drawOn(c, 50, y_position)

    # Información adicional
    c.setFont("Helvetica", 10)
    c.drawString(50, 60, "Gracias por su compra!")
    c.drawString(50, 45, "Este documento sirve como comprobante de pago.")
    c.drawRightString(width - 50, 45, f"Recibo: {timestamp}")

    c.save()

    return pdf_filename


@app.route('/pagar', methods=['GET', 'POST'])
@login_required
def pagar():
    """Página para simular pago. En POST valida datos mínimos y genera recibo."""
    if request.method == 'GET':
        return render_template('pagar.html')

    # POST: procesar datos de la tarjeta (simulado)
    titular = request.form.get('titular')
    numero = request.form.get('numero', '').replace(' ', '')
    cvv = request.form.get('cvv')

    # Validaciones simples (no reales)
    errors = []
    if not titular or len(titular) < 3:
        errors.append('Nombre del titular inválido')
    if not numero.isdigit() or not (13 <= len(numero) <= 19):
        errors.append('Número de tarjeta inválido')
    if not cvv.isdigit() or not (3 <= len(cvv) <= 4):
        errors.append('CVV inválido')

    if errors:
        for e in errors:
            flash(e, 'danger')
        return redirect(url_for('pagar'))

    try:
        # Simular procesamiento (siempre exitoso en esta simulación)
        conexion = get_db()
        items_carrito = CarritoModel.get_carrito_by_usuario(conexion, current_user.id)
        if not items_carrito:
            flash('No hay items en el carrito', 'warning')
            return redirect(url_for('ver_carrito'))

        # Generar el PDF y limpiar carrito
        pdf_filename = _generate_pdf_for_items(items_carrito, current_user)
        CarritoModel.limpiar_carrito(conexion, current_user.id)

        # Mostrar página que abre el recibo en nueva pestaña y redirige
        return render_template('pago_exitoso.html', pdf_filename=pdf_filename)
    except Exception as ex:
        app.logger.exception('Error al procesar pago/generar recibo:')
        flash('Ocurrió un error al procesar el pago. Intente nuevamente.', 'danger')
        return redirect(url_for('ver_carrito'))

@app.route('/carrito/limpiar', methods=['POST'])
@login_required
def limpiar_carrito():
    try:
        conexion = get_db()
        CarritoModel.limpiar_carrito(conexion, current_user.id)
        flash("Carrito limpiado", "success")
    except Exception as e:
        flash(f"Error al limpiar carrito: {str(e)}", 'danger')
    
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
        password_new = request.form[FORM_CONTRASEÑA]
        confirmar = request.form['confirmar']

        if password_new != confirmar:
            flash('Las contraseñas no coinciden.', 'danger')
            return render_template(RECUPERAR_TEMPLATE, correo=correo)

        hash_nueva_contrasena = generate_password_hash(password_new)
        user_to_update = Usuario(id=None, nombre=None, correo=correo, password=hash_nueva_contrasena)

        try:
            # Delegar la actualización al modelo
            UserModel.update_password(conexion, user_to_update)
            flash('Has cambiado tu contraseña exitosamente. Ahora puedes iniciar sesión.', 'success')
            return redirect(url_for('login'))
        except Exception as e:
            flash(f"Error al recuperar contraseña: {str(e)}", 'danger')
            return render_template(RECUPERAR_TEMPLATE, correo=correo)
             
    return render_template(RECUPERAR_TEMPLATE)

if __name__ == '__main__':
    app.run(debug=True)

