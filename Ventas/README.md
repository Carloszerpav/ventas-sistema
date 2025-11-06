# Sistema de Registro de Ventas

Una aplicación web moderna y intuitiva para el registro y gestión de ventas, desarrollada con Python Flask.

## 🚀 Características

### Funcionalidades Principales
- ✅ **Registro de ventas** con cliente/producto, valor total y abono
- ✅ **Cálculo automático** del saldo pendiente
- ✅ **Selección múltiple de rubros** (Maquillaje, Renacer, Tendencia, Accesorios, Zapatos)
- ✅ **Fecha automática** con opción de modificación manual
- ✅ **Estadísticas en tiempo real** por rubro y generales
- ✅ **Autenticación con Google OAuth**
- ✅ **Gestión de pagos** y historial
- ✅ **Cierre mensual** de estadísticas
- ✅ **Interfaz responsive** y moderna

### Características Técnicas
- 🎨 **Diseño moderno** con Material Design
- 📱 **Responsive** para dispositivos móviles y escritorio
- ⚡ **Validación en tiempo real** de formularios
- 🔄 **Cálculos automáticos** de saldos pendientes
- 📊 **Estadísticas visuales** con gráficos por rubro
- 🎯 **UX optimizada** con animaciones suaves
- 🔒 **Validaciones robustas** de datos
- 💾 **Base de datos PostgreSQL** para producción

## 📋 Requisitos

- Python 3.9 o superior
- pip (gestor de paquetes de Python)

## 🛠️ Instalación Local

1. **Clonar o descargar el proyecto**
   ```bash
   cd Ventas
   ```

2. **Instalar dependencias**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configurar variables de entorno**
   Crea un archivo `.env` (no incluido en el repositorio) con:
   ```
   SECRET_KEY=tu_clave_secreta_aqui
   GOOGLE_CLIENT_ID=tu_client_id_de_google
   GOOGLE_CLIENT_SECRET=tu_client_secret_de_google
   DATABASE_URL=sqlite:///ventas.db
   ```

4. **Ejecutar la aplicación**
   ```bash
   python app.py
   ```

5. **Abrir en el navegador**
   ```
   http://localhost:5000
   ```

## 🚂 Despliegue en Railway

### Pasos para Desplegar

1. **Crear cuenta en Railway**
   - Ve a [railway.app](https://railway.app)
   - Inicia sesión con tu cuenta de GitHub

2. **Subir el proyecto a GitHub**
   ```bash
   git init
   git add .
   git commit -m "Initial commit"
   git branch -M main
   git remote add origin https://github.com/tu-usuario/tu-repositorio.git
   git push -u origin main
   ```

3. **Conectar con Railway**
   - En Railway, haz clic en "New Project"
   - Selecciona "Deploy from GitHub repo"
   - Conecta tu repositorio

4. **Configurar Variables de Entorno**
   En Railway, ve a la pestaña "Variables" y agrega:
   - `SECRET_KEY`: Genera una clave secreta (puedes usar: `python -c "import secrets; print(secrets.token_hex(32))"`)
   - `GOOGLE_CLIENT_ID`: Tu Client ID de Google OAuth
   - `GOOGLE_CLIENT_SECRET`: Tu Client Secret de Google OAuth
   - `DATABASE_URL`: Se configura automáticamente cuando agregas un servicio PostgreSQL

5. **Agregar Base de Datos PostgreSQL**
   - En tu proyecto de Railway, haz clic en "+ New"
   - Selecciona "Database" → "Add PostgreSQL"
   - Railway configurará automáticamente `DATABASE_URL`

6. **Desplegar**
   - Railway detectará automáticamente la configuración en `nixpacks.toml` y `railway.json`
   - El despliegue comenzará automáticamente
   - Espera a que termine el build

7. **Generar Dominio**
   - En la pestaña "Settings" → "Networking"
   - Haz clic en "Generate Domain" para obtener una URL pública

### Archivos de Configuración

El proyecto incluye los siguientes archivos de configuración para Railway:

- `nixpacks.toml`: Configuración del builder de Railway
- `railway.json`: Configuración de despliegue y comandos de inicio
- `requirements.txt`: Dependencias de Python

## 📖 Uso

### Registro de Ventas
1. **Cliente/Producto**: Ingresa el nombre del cliente o producto
2. **Fecha**: Se autocompleta con la fecha actual (modificable)
3. **Valor Total**: Ingresa el valor total de la venta
4. **Abono**: Ingresa el monto abonado
5. **Rubros**: Selecciona uno o varios rubros usando los checkboxes
6. **Saldo Pendiente**: Se calcula automáticamente
7. **Registrar**: Haz clic en "Registrar Venta"

### Gestión de Ventas
- **Ver todas las ventas** en la tabla principal
- **Eliminar ventas** con el botón de papelera
- **Registrar pagos** adicionales
- **Ver historial** de pagos por venta
- **Ver estadísticas** en tiempo real
- **Cerrar mes** excluyendo ventas cerradas de estadísticas
- **Buscar ventas** por nombre de cliente

## 🏗️ Estructura del Proyecto

```
Ventas/
├── app.py                 # Aplicación principal Flask
├── requirements.txt       # Dependencias de Python
├── nixpacks.toml         # Configuración de Railway (Nixpacks)
├── railway.json          # Configuración de Railway
├── .gitignore           # Archivos ignorados por Git
├── README.md            # Este archivo
├── templates/           # Plantillas HTML
│   ├── index.html
│   ├── login.html
│   ├── pago.html
│   ├── historial.html
│   ├── cierre_mensual.html
│   ├── ventas_excluidas.html
│   ├── estadisticas_periodo.html
│   ├── privacy.html
│   └── terms.html
└── static/              # Archivos estáticos
    ├── css/
    │   └── style.css
    └── js/
        └── script.js
```

## 🎨 Rubros Disponibles

- **Maquillaje**: Productos de belleza y cosméticos
- **Renacer**: Productos de cuidado personal
- **Tendencia**: Productos de moda actual
- **Accesorios**: Complementos y accesorios
- **Zapatos**: Calzado y zapatillas

## 📊 Estadísticas

La aplicación muestra estadísticas en tiempo real:

- **Total de ventas** registradas
- **Valor total** de todas las ventas
- **Total abonado** en todas las ventas
- **Saldo pendiente** total
- **Estadísticas por rubro** con desglose detallado
- **Estadísticas por período** con gráficos

## 🔧 Personalización

### Agregar Nuevos Rubros
Edita el archivo `app.py` y modifica la lista `RUBROS`:

```python
RUBROS = ['Maquillaje', 'Renacer', 'Tendencia', 'Accesorios', 'Zapatos', 'Nuevo Rubro']
```

### Cambiar Moneda
En `app.py`, modifica la función `formatear_moneda`:

```python
def formatear_moneda(valor):
    return f"€{valor:,.2f}"  # Para euros
```

## 🔒 Seguridad

- Las credenciales de OAuth se manejan mediante variables de entorno
- La clave secreta se genera automáticamente si no se proporciona (no recomendado para producción)
- Los datos están asociados al usuario autenticado
- La base de datos usa PostgreSQL en producción

## 📝 Notas

- La aplicación usa SQLite para desarrollo local y PostgreSQL para producción
- Las variables de entorno son obligatorias para el funcionamiento en producción
- La base de datos se inicializa automáticamente al iniciar la aplicación

---

**Desarrollado con ❤️ usando Python Flask**
