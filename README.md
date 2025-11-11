# 🛍️ E-commerce Final POO-I

[![Python](https://img.shields.io/badge/Python-3.9+-3776ab.svg)](https://www.python.org/)
[![Flask](https://img.shields.io/badge/Flask-2.0+-000000.svg)](https://flask.palletsprojects.com/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-12+-336791.svg)](https://www.postgresql.org/)
[![Grade](https://img.shields.io/badge/Grade-4.72%2F5.0-brightgreen.svg)](https://github.com/Kepler11145123)

Plataforma de e-commerce completa con Flask, PostgreSQL y Programación Orientada a Objetos.

**Calificación: 4.72/5.0 (94.3%) - Muy Adecuado** ✅

## 🚀 Inicio Rápido

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

## 📁 Estructura

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
├── base.html
├── login.html
├── catalogo.html
├── carrito.html
├── pedidos.html
└── admin/

static/              # Estilos e imágenes
├── css/style.css
├── js/script.js
└── images/

app.py              # Aplicación principal
requirements.txt    # Dependencias
```

## ✨ Características

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

## 🏗️ Arquitectura MVC

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

## 📊 Base de Datos

**Tablas:**
- `usuarios` - Cliente/Administrador
- `productos` - Catálogo
- `carrito` - Items en carrito
- `pedidos` - Cabecera de pedidos
- `detalle_pedidos` - Items por pedido

**Triggers:**
- Actualizar stock automáticamente al crear pedido

## 🔒 Seguridad

- Contraseñas hasheadas con Werkzeug
- CSRF tokens en todos los formularios
- SQL queries con placeholders
- Control de roles en endpoints
- Validaciones servidor-side
- Transacciones con rollback
- Variables de entorno para secrets

## 🔌 Rutas Principales

| Ruta | Método | Descripción |
|------|--------|-----------|
| `/login` | GET/POST | Autenticación |
| `/registro` | GET/POST | Crear cuenta |
| `/catalogo` | GET | Ver productos |
| `/carrito` | GET | Ver carrito |
| `/crear-pedido` | POST | Comprar |
| `/mis-pedidos` | GET | Historial |
| `/admin/dashboard` | GET | Admin (admin only) |

## 📦 Dependencias

```
Flask==2.3.0
psycopg2-binary==2.9.6
Flask-Login==0.6.2
Flask-WTF==1.1.1
Werkzeug==2.3.0
python-dotenv==1.0.0
```

Ver `requirements.txt` completo

## 🐛 Troubleshooting

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

## 🎓 Conceptos POO Implementados

- **Herencia:** Usuario → Cliente/Administrador
- **Encapsulación:** Atributos privados, métodos públicos
- **Polimorfismo:** Métodos sobrecargados
- **Abstracción:** Clases modelo y entidad
- **Composición:** Models que usan Entities

## 📚 Documentación Adicional

- [QUICKSTART.md](QUICKSTART.md) - Guía paso a paso
- [.env.example](.env.example) - Variables de entorno
- [.gitignore](.gitignore) - Archivos ignorados

## 🚀 Mejoras Futuras

- [ ] Sistema de ratings/reseñas
- [ ] Cupones y descuentos
- [ ] Integración Stripe/PayPal
- [ ] Notificaciones email
- [ ] Búsqueda avanzada
- [ ] Tests con pytest
- [ ] API REST documentada
- [ ] Docker

## 👤 Autor

**Kepler11145123** - [@GitHub](https://github.com/Kepler11145123)

## 📄 Licencia

MIT - Ver LICENSE

---

**Calificación:** 4.72/5.0 ⭐ **Muy Adecuado**
- Contenido: 4.58/5.0
- Framework: 4.75/5.0
- Impacto: 4.79/5.0

**Última actualización:** 11 de Noviembre de 2025
