# 🛍️ E-commerce Final POO-I
Plataforma de e-commerce completa con Flask, PostgreSQL y Programación Orientada a Objetos.
## Inicio Rápido

### Requisitos
- Python 3.9+
- PostgreSQL 12+
- pip

### Instalación

```bash
# Clonar
git clone https://github.com/Kepler11145123/ProyectoFinalPOO1.git
cd ProyectoFinalPOO1

# Entorno virtual
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Dependencias
pip install -r requirements.txt

# Base de datos
psql -U postgres -c "CREATE DATABASE ecommerce_db;"

# Configurar .env
cp .env.example .env
# Editar DATABASE_URL en .env

# Ejecutar
python app.py
```

Accede a: `http://localhost:5000`

##  Estructura

```
models/
├── entities/          # Modelos de dominio
│   ├── usuario.py
│   ├── producto.py
│   └── pedido.py
└── [Models]          # Acceso a BD
    ├── UserModel.py
    ├── ProductoModel.py
    ├── CarritoModel.py
    └── PedidoModel.py

templates/            # Vistas HTML
├── carrito_compras.html
├── catalogo.html
├── inicio.html
├── login.html
├── pagar.html
├── pago_exitoso.html
├── recuperar.html
├── registro.html
└── admin/editar_pedido.html
└── admin/panel_admin.html
└── admin/form_producto.html
└── admin/detalle_pedido.html
└── admin/buscar_pedidos.html


static/              # Estilos e imágenes
├── auth.css
├── buscar_pedidos.css
├── carrito.css
├── detalle_pedido.css
├── editar_pedido.css
├── editar_producto.css
├── inicio.css
├── panel_admin.css
├── style.css
├── js/script.js
└── images/

app.py              # Aplicación principal
requirements.txt    # Dependencias
```

##  Características

- ✅ **Autenticación segura** con hashing de contraseñas
- ✅ **Roles** (Cliente/Admin) con control de permisos
- ✅ **Carrito inteligente** con control de stock
- ✅ **CRUD de productos** en panel admin
- ✅ **Sistema de pedidos** con transacciones ACID
- ✅ **Facturas** automatizadas
- ✅ **Soft delete** para datos importantes
- ✅ **Triggers BD** para actualizar stock
- ✅ **Protección CSRF** en formularios
- ✅ **Prevención SQL Injection** con placeholders

##  Arquitectura MVC

```
Flask App (app.py)
    ↓
Templates (HTML/CSS/JS)
    ↓
Models (Acceso BD)
    ↓
Entities (Objetos dominio)
    ↓
PostgreSQL
```

##  Base de Datos

**Tablas:**
- `usuarios` - Cliente/Administrador
- `productos` - Catálogo
- `carrito` - Items en carrito
- `pedidos` - Cabecera de pedidos
- `detalle_pedidos` - Items por pedido

**Triggers:**
- Actualizar stock automáticamente al crear pedido

##  Seguridad

- Contraseñas hasheadas con Werkzeug
- CSRF tokens en todos los formularios
- SQL queries con placeholders
- Control de roles en endpoints
- Validaciones servidor-side
- Transacciones con rollback
- Variables de entorno para secrets

##  Rutas Principales

| Ruta | Método | Descripción |
|------|--------|-----------|
| `/login` | GET/POST | Autenticación |
| `/registro` | GET/POST | Crear cuenta |
| `/catalogo` | GET | Ver productos |
| `/carrito` | GET | Ver carrito |
| `/crear-pedido` | POST | Comprar |
| `/mis-pedidos` | GET | Historial |
| `/admin/dashboard` | GET | Admin (admin only) |

##  Dependencias

```
blinker==1.9.0
click==8.3.0
colorama==0.4.6
Flask==3.1.2
Flask-Login==0.6.3
Flask-WTF==1.2.2
gunicorn==23.0.0
itsdangerous==2.2.0
Jinja2==3.1.6
MarkupSafe==3.0.3
packaging==25.0
psycopg2==2.9.11
python-dotenv==1.1.1
Werkzeug==3.1.3
WTForms==3.2.1
reportlab==3.6.13

```

Ver `requirements.txt` completo

##  Troubleshooting

### Error de conexión BD
```bash
# Verificar PostgreSQL está corriendo
psql -U postgres

# Verificar DATABASE_URL en .env
echo $DATABASE_URL
```

### ModuleNotFoundError
```bash
source venv/bin/activate
pip install -r requirements.txt
```

### CSRF token missing
Asegurar formularios tengan:
```html
<input type="hidden" name="csrf_token" value="{{ csrf_token() }}">
```

##  Conceptos POO Implementados

- **Herencia:** Usuario → Cliente/Administrador
- **Encapsulación:** Atributos privados, métodos públicos
- **Polimorfismo:** Métodos sobrecargados
- **Abstracción:** Clases modelo y entidad
- **Composición:** Models que usan Entities

##  Documentación Adicional
**Última actualización:** 11 de Noviembre de 2025
