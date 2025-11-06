from flask import Flask, request, redirect, url_for, render_template, jsonify, session
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from authlib.integrations.flask_client import OAuth
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import json
import os
import secrets

app = Flask(__name__)
# Clave secreta: usar variable de entorno en producción, generar aleatoria en desarrollo
app.secret_key = os.environ.get('SECRET_KEY', secrets.token_hex(16))

# Configurar HTTPS en producción (Railway)
# Railway pasa el tráfico a través de un proxy que maneja HTTPS
# Si está en producción (no localhost), usar HTTPS
if os.environ.get('RAILWAY_ENVIRONMENT') or os.environ.get('RAILWAY_ENVIRONMENT_NAME') or os.environ.get('PORT'):
    # En Railway, forzar HTTPS
    app.config['PREFERRED_URL_SCHEME'] = 'https'
    # Usar ProxyFix para detectar correctamente el protocolo desde los headers
    from werkzeug.middleware.proxy_fix import ProxyFix
    app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)

# ========================================
# CONFIGURACIÓN DE BASE DE DATOS
# ========================================
# Configuración flexible: SQLite para desarrollo, PostgreSQL para producción
DATABASE_URL = os.environ.get('DATABASE_URL', 'sqlite:///ventas.db')

# Si es PostgreSQL (Railway), necesita ajustes en la URL
if DATABASE_URL.startswith('postgres://'):
    DATABASE_URL = DATABASE_URL.replace('postgres://', 'postgresql://', 1)

app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URL
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Inicializar SQLAlchemy
db = SQLAlchemy(app)

# Configuración de Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message = 'Por favor inicia sesión para acceder a esta página.'
login_manager.login_message_category = 'info'

# Configuración de OAuth con Google
oauth = OAuth(app)

# Configuración de Google OAuth
# Credenciales desde variables de entorno (seguridad)
GOOGLE_CLIENT_ID = os.environ.get('GOOGLE_CLIENT_ID', '')
GOOGLE_CLIENT_SECRET = os.environ.get('GOOGLE_CLIENT_SECRET', '')

if not GOOGLE_CLIENT_ID or not GOOGLE_CLIENT_SECRET:
    print("⚠️ ADVERTENCIA: GOOGLE_CLIENT_ID y GOOGLE_CLIENT_SECRET deben estar configuradas como variables de entorno")

google = oauth.register(
    name='google',
    client_id=GOOGLE_CLIENT_ID,
    client_secret=GOOGLE_CLIENT_SECRET,
    server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
    client_kwargs={
        'scope': 'openid email profile'
    }
)

# Clase de Usuario para Flask-Login
class User(UserMixin):
    def __init__(self, id, email, name, picture):
        self.id = id
        self.email = email
        self.name = name
        self.picture = picture

@login_manager.user_loader
def load_user(user_id):
    # En una aplicación real, esto cargaría el usuario de una base de datos
    # Por ahora, usamos la sesión
    if 'user' in session:
        user_data = session['user']
        return User(
            id=user_data['id'],
            email=user_data['email'],
            name=user_data['name'],
            picture=user_data.get('picture', '')
        )
    return None

# ========================================
# MODELOS DE BASE DE DATOS
# ========================================

class Venta(db.Model):
    """Modelo de Venta en la base de datos"""
    __tablename__ = 'venta'
    
    id = db.Column(db.Integer, primary_key=True)
    usuario_email = db.Column(db.String(255), nullable=False, index=True)
    cliente = db.Column(db.String(255), nullable=False)
    valor_total = db.Column(db.Numeric(10, 2), nullable=False)
    abono = db.Column(db.Numeric(10, 2), nullable=False, default=0)
    saldo_pendiente = db.Column(db.Numeric(10, 2), nullable=False)
    fecha = db.Column(db.String(10), nullable=False)  # YYYY-MM-DD
    fecha_registro = db.Column(db.String(19), nullable=False)  # YYYY-MM-DD HH:MM
    estado = db.Column(db.String(20), nullable=False, default='Activa')
    incluida_en_estadisticas = db.Column(db.Boolean, nullable=False, default=True)
    mes_cierre = db.Column(db.String(7), nullable=True)  # YYYY-MM
    
    # Relaciones
    pagos = db.relationship('Pago', backref='venta', lazy=True, cascade='all, delete-orphan')
    rubros = db.relationship('VentaRubro', backref='venta', lazy=True, cascade='all, delete-orphan')
    
    def to_dict(self):
        """Convierte la venta a diccionario para compatibilidad con código existente"""
        return {
            'id': self.id,
            'cliente': self.cliente,
            'valor_total': float(self.valor_total),
            'abono': float(self.abono),
            'saldo_pendiente': float(self.saldo_pendiente),
            'rubros': [vr.rubro for vr in self.rubros] if hasattr(self, 'rubros') else [],
            'fecha': self.fecha,
            'fecha_registro': self.fecha_registro,
            'estado': self.estado,
            'historial_pagos': [p.to_dict() for p in self.pagos],
            'total_pagos': len(self.pagos),
            'incluida_en_estadisticas': self.incluida_en_estadisticas,
            'mes_cierre': self.mes_cierre
        }

class Pago(db.Model):
    """Modelo de Pago en la base de datos"""
    __tablename__ = 'pago'
    
    id = db.Column(db.Integer, primary_key=True)
    venta_id = db.Column(db.Integer, db.ForeignKey('venta.id', ondelete='CASCADE'), nullable=False)
    monto = db.Column(db.Numeric(10, 2), nullable=False)
    fecha = db.Column(db.String(19), nullable=False)  # YYYY-MM-DD HH:MM
    tipo = db.Column(db.String(50), nullable=False, default='Abono')
    
    def to_dict(self):
        """Convierte el pago a diccionario"""
        return {
            'id': self.id,
            'monto': float(self.monto),
            'fecha': self.fecha,
            'tipo': self.tipo
        }

class VentaRubro(db.Model):
    """Modelo para almacenar los rubros de cada venta"""
    __tablename__ = 'venta_rubro'
    
    id = db.Column(db.Integer, primary_key=True)
    venta_id = db.Column(db.Integer, db.ForeignKey('venta.id', ondelete='CASCADE'), nullable=False)
    rubro = db.Column(db.String(50), nullable=False)
    
    # Índice único para evitar duplicados
    __table_args__ = (db.UniqueConstraint('venta_id', 'rubro', name='unique_venta_rubro'),)

# ========================================
# SISTEMA DE VENTAS - Carloszerpav
# ========================================
# Este es mi sistema de gestión de ventas personal
# Lo hice para manejar mis ventas de manera fácil y rápida
# - Carloszerpav

# Mis rubros de trabajo - Carloszerpav
RUBROS = ['Maquillaje', 'Renacer', 'Tendencia', 'Accesorios', 'Zapatos']

def agregar_venta(usuario_email, cliente, valor_total, abono, rubros, fecha=None):
    """
    Función para agregar una nueva venta - Carloszerpav
    Ahora guarda en base de datos y asocia con el usuario
    """
    try:
        # Validar y limpiar datos
        usuario_email = str(usuario_email).strip() if usuario_email else ""
        if not usuario_email:
            raise ValueError("El email del usuario es requerido")
        
        cliente = str(cliente).strip() if cliente else ""
        valor_total = float(valor_total) if valor_total else 0.0
        abono = float(abono) if abono else 0.0
        rubros = list(rubros) if rubros else []
        
        # Validación obligatoria de rubros - Carloszerpav
        if not rubros:
            raise ValueError("Debe seleccionar al menos un rubro")
        
        # Validar que los rubros seleccionados sean válidos
        rubros_validos = [rubro for rubro in rubros if rubro in RUBROS]
        if not rubros_validos:
            raise ValueError("Los rubros seleccionados no son válidos")
        
        # Obtener fecha actual si no se proporciona
        if not fecha:
            fecha = datetime.now().strftime("%Y-%m-%d")
        
        fecha_registro = datetime.now().strftime("%Y-%m-%d %H:%M")
        
        # Calcular saldo pendiente
        saldo_pendiente = valor_total - abono
        estado = 'Activa' if saldo_pendiente > 0 else 'Cerrada'
        
        # Crear la venta en la base de datos
        nueva_venta = Venta(
            usuario_email=usuario_email,
            cliente=cliente,
            valor_total=valor_total,
            abono=abono,
            saldo_pendiente=saldo_pendiente,
            fecha=fecha,
            fecha_registro=fecha_registro,
            estado=estado,
            incluida_en_estadisticas=True,
            mes_cierre=None
        )
        
        db.session.add(nueva_venta)
        db.session.flush()  # Para obtener el ID
        
        # Agregar rubros
        for rubro in rubros_validos:
            venta_rubro = VentaRubro(venta_id=nueva_venta.id, rubro=rubro)
            db.session.add(venta_rubro)
        
        # Si hay abono inicial, crear pago
        if abono > 0:
            pago_inicial = Pago(
                venta_id=nueva_venta.id,
                monto=abono,
                fecha=fecha_registro,
                tipo='Pago inicial'
            )
            db.session.add(pago_inicial)
        
        db.session.commit()
        
        # Retornar como diccionario para compatibilidad
        return nueva_venta.to_dict()
        
    except Exception as e:
        db.session.rollback()
        print(f"❌ Error en agregar_venta: {e}")
        raise e

def eliminar_venta(usuario_email, venta_id):
    """
    Elimina una venta de la base de datos
    Args:
        usuario_email (str): Email del usuario (para seguridad)
        venta_id (int): El ID de la venta a eliminar
    Returns:
        bool: True si se encontró y eliminó la venta, False si no existe
    """
    venta = Venta.query.filter_by(id=venta_id, usuario_email=usuario_email).first()
    if venta:
        db.session.delete(venta)
        db.session.commit()
        return True
    return False

def obtener_venta(usuario_email, venta_id):
    """
    Obtiene una venta específica por ID y usuario
    Args:
        usuario_email (str): Email del usuario (para seguridad)
        venta_id (int): El ID de la venta
    Returns:
        dict: La venta encontrada o None si no existe o no pertenece al usuario
    """
    venta = Venta.query.filter_by(id=venta_id, usuario_email=usuario_email).first()
    if venta:
        return venta.to_dict()
    return None

def registrar_pago(usuario_email, venta_id, monto_pago, tipo_pago="Abono"):
    """
    Registra un pago adicional para una venta
    Args:
        usuario_email (str): Email del usuario (para seguridad)
        venta_id (int): ID de la venta
        monto_pago (float): Monto del pago
        tipo_pago (str): Tipo de pago (Abono, Cuota, etc.)
    Returns:
        dict: La venta actualizada o None si no se encuentra
    """
    venta = Venta.query.filter_by(id=venta_id, usuario_email=usuario_email).first()
    if not venta:
        return None
    
    if venta.estado == 'Cerrada':
        raise ValueError("No se pueden registrar pagos en ventas cerradas")
    
    if monto_pago <= 0:
        raise ValueError("El monto del pago debe ser mayor a 0")
    
    if float(monto_pago) > float(venta.saldo_pendiente):
        raise ValueError("El monto del pago no puede ser mayor al saldo pendiente")
    
    try:
        # Crear nuevo pago en la base de datos
        fecha_pago = datetime.now().strftime("%Y-%m-%d %H:%M")
        nuevo_pago = Pago(
            venta_id=venta_id,
            monto=monto_pago,
            fecha=fecha_pago,
            tipo=tipo_pago
        )
        
        db.session.add(nuevo_pago)
        
        # Actualizar totales de la venta (convertir a float para operaciones, luego a Decimal)
        from decimal import Decimal
        abono_actual = float(venta.abono)
        saldo_actual = float(venta.saldo_pendiente)
        
        nuevo_abono = abono_actual + float(monto_pago)
        nuevo_saldo = saldo_actual - float(monto_pago)
        
        # Asignar los nuevos valores (SQLAlchemy convertirá automáticamente a Numeric)
        venta.abono = Decimal(str(nuevo_abono)).quantize(Decimal('0.01'))
        venta.saldo_pendiente = Decimal(str(nuevo_saldo)).quantize(Decimal('0.01'))
        
        # Verificar si la venta se completa
        if nuevo_saldo <= 0:
            venta.estado = 'Cerrada'
            venta.saldo_pendiente = Decimal('0.00')
        
        db.session.commit()
        
        # Retornar como diccionario
        return venta.to_dict()
        
    except Exception as e:
        db.session.rollback()
        print(f"❌ Error en registrar_pago: {e}")
        raise e

def obtener_estadisticas(usuario_email):
    """
    Función para obtener estadísticas - Carloszerpav
    Ahora filtra por usuario y usa base de datos
    """
    # Obtener todas las ventas del usuario desde BD
    todas_ventas = Venta.query.filter_by(usuario_email=usuario_email).all()
    
    # Convertir a diccionarios para compatibilidad
    ventas_dict = [v.to_dict() for v in todas_ventas]
    
    # Ventas incluidas en estadísticas
    ventas_en_estadisticas = [v for v in ventas_dict if v.get('incluida_en_estadisticas', True)]
    ventas_activas = [v for v in ventas_en_estadisticas if v['estado'] == 'Activa']
    ventas_cerradas = [v for v in ventas_en_estadisticas if v['estado'] == 'Cerrada']
    ventas_excluidas = [v for v in ventas_dict if not v.get('incluida_en_estadisticas', True)]
    
    total_ventas_activas = len(ventas_activas)
    total_valor_activas = sum(v['valor_total'] for v in ventas_activas)
    total_abonado_activas = sum(v['abono'] for v in ventas_activas)
    total_pendiente_activas = sum(v['saldo_pendiente'] for v in ventas_activas)
    
    # Estadísticas por rubro
    estadisticas_rubros = {}
    for rubro in RUBROS:
        ventas_rubro = [v for v in ventas_en_estadisticas if rubro in v['rubros']]
        estadisticas_rubros[rubro] = {
            'cantidad': len(ventas_rubro),
            'valor_total': sum(v['valor_total'] for v in ventas_rubro),
            'abonado': sum(v['abono'] for v in ventas_rubro),
            'pendiente': sum(v['saldo_pendiente'] for v in ventas_rubro)
        }
    
    return {
        'total_ventas_activas': total_ventas_activas,
        'total_ventas_cerradas': len(ventas_cerradas),
        'total_ventas_excluidas': len(ventas_excluidas),
        'total_ventas': len(todas_ventas),
        'total_valor': total_valor_activas,
        'total_abonado': total_abonado_activas,
        'total_pendiente': total_pendiente_activas,
        'por_rubro': estadisticas_rubros
    }

def formatear_fecha(fecha_str):
    """
    Formatea una fecha para mostrar
    Args:
        fecha_str (str): Fecha en formato YYYY-MM-DD
    Returns:
        str: Fecha formateada
    """
    try:
        fecha = datetime.strptime(fecha_str, "%Y-%m-%d")
        return fecha.strftime("%d/%m/%Y")
    except:
        return fecha_str

def formatear_moneda(valor):
    """
    Función para formatear moneda - Carloszerpav
    Me ayuda a mostrar los precios de manera bonita
    """
    return f"${valor:,.2f}"

def cerrar_mes_estadisticas(usuario_email, mes=None, año=None):
    """
    Cierra las estadísticas del mes especificado, excluyendo las ventas cerradas
    Args:
        usuario_email (str): Email del usuario
        mes (int): Mes a cerrar (1-12). Si es None, usa el mes actual
        año (int): Año a cerrar. Si es None, usa el año actual
    Returns:
        dict: Resumen del cierre mensual
    """
    if mes is None:
        mes = datetime.now().month
    if año is None:
        año = datetime.now().year
    
    # Obtener ventas cerradas del usuario que aún están en estadísticas
    ventas_a_excluir = Venta.query.filter_by(
        usuario_email=usuario_email,
        estado='Cerrada',
        incluida_en_estadisticas=True
    ).all()
    
    # Calcular totales antes de actualizar
    total_excluidas = len(ventas_a_excluir)
    valor_total_excluido = sum(float(v.valor_total) for v in ventas_a_excluir)
    valor_abonado_excluido = sum(float(v.abono) for v in ventas_a_excluir)
    
    # Marcar ventas como excluidas de estadísticas
    mes_cierre_str = f"{año}-{mes:02d}"
    for venta in ventas_a_excluir:
        venta.incluida_en_estadisticas = False
        venta.mes_cierre = mes_cierre_str
    
    db.session.commit()
    
    resumen = {
        'mes': mes,
        'año': año,
        'ventas_excluidas': total_excluidas,
        'valor_total_excluido': valor_total_excluido,
        'valor_abonado_excluido': valor_abonado_excluido,
        'fecha_cierre': datetime.now().strftime("%Y-%m-%d %H:%M")
    }
    
    print(f"✅ Cierre mensual {mes}/{año}: {total_excluidas} ventas excluidas")
    return resumen

def obtener_ventas_cerradas_pendientes(usuario_email):
    """
    Obtiene las ventas cerradas que aún están incluidas en estadísticas
    Args:
        usuario_email (str): Email del usuario
    Returns:
        list: Lista de ventas cerradas pendientes de cierre mensual
    """
    ventas_db = Venta.query.filter_by(
        usuario_email=usuario_email,
        estado='Cerrada',
        incluida_en_estadisticas=True
    ).all()
    
    return [venta.to_dict() for venta in ventas_db]

def obtener_estadisticas_por_periodo(usuario_email, fecha_inicio, fecha_fin):
    """
    Obtiene estadísticas de ventas en un período específico
    Args:
        usuario_email (str): Email del usuario
        fecha_inicio (str): Fecha de inicio en formato YYYY-MM-DD
        fecha_fin (str): Fecha de fin en formato YYYY-MM-DD
    Returns:
        dict: Estadísticas del período
    """
    try:
        # Convertir fechas a objetos datetime para comparación
        inicio = datetime.strptime(fecha_inicio, "%Y-%m-%d")
        fin = datetime.strptime(fecha_fin, "%Y-%m-%d")
        
        # Obtener todas las ventas del usuario en el período
        todas_ventas = Venta.query.filter_by(usuario_email=usuario_email).all()
        
        # Filtrar ventas en el período
        ventas_periodo = []
        for venta in todas_ventas:
            fecha_venta = datetime.strptime(venta.fecha, "%Y-%m-%d")
            if inicio <= fecha_venta <= fin:
                ventas_periodo.append(venta.to_dict())
        
        # Calcular estadísticas
        total_ventas = len(ventas_periodo)
        total_valor = sum(v['valor_total'] for v in ventas_periodo)
        total_abonado = sum(v['abono'] for v in ventas_periodo)
        total_pendiente = sum(v['saldo_pendiente'] for v in ventas_periodo)
        
        # Ventas por estado
        ventas_activas = [v for v in ventas_periodo if v['estado'] == 'Activa']
        ventas_cerradas = [v for v in ventas_periodo if v['estado'] == 'Cerrada']
        
        # Estadísticas por rubro
        estadisticas_rubros = {}
        for rubro in RUBROS:
            ventas_rubro = [v for v in ventas_periodo if rubro in v['rubros']]
            estadisticas_rubros[rubro] = {
                'cantidad': len(ventas_rubro),
                'valor_total': sum(v['valor_total'] for v in ventas_rubro),
                'abonado': sum(v['abono'] for v in ventas_rubro),
                'pendiente': sum(v['saldo_pendiente'] for v in ventas_rubro)
            }
        
        # Ventas por día (para gráfica)
        ventas_por_dia = {}
        for venta in ventas_periodo:
            dia = venta['fecha']
            if dia not in ventas_por_dia:
                ventas_por_dia[dia] = {
                    'cantidad': 0,
                    'valor_total': 0,
                    'abonado': 0
                }
            ventas_por_dia[dia]['cantidad'] += 1
            ventas_por_dia[dia]['valor_total'] += venta['valor_total']
            ventas_por_dia[dia]['abonado'] += venta['abono']
        
        # Ordenar por fecha
        ventas_por_dia_ordenado = dict(sorted(ventas_por_dia.items()))
        
        return {
            'fecha_inicio': fecha_inicio,
            'fecha_fin': fecha_fin,
            'total_ventas': total_ventas,
            'total_valor': total_valor,
            'total_abonado': total_abonado,
            'total_pendiente': total_pendiente,
            'ventas_activas': len(ventas_activas),
            'ventas_cerradas': len(ventas_cerradas),
            'por_rubro': estadisticas_rubros,
            'por_dia': ventas_por_dia_ordenado,
            'ventas_detalle': ventas_periodo
        }
        
    except Exception as e:
        print(f"❌ Error en estadísticas por período: {e}")
        return None

# ========================================
# RUTAS DE AUTENTICACIÓN
# ========================================

@app.route('/login')
def login():
    """
    Página de inicio de sesión
    """
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    return render_template('login.html')

@app.route('/login/google')
def login_google():
    """
    Inicia el proceso de autenticación con Google
    """
    redirect_uri = url_for('auth_callback', _external=True)
    return google.authorize_redirect(redirect_uri)

@app.route('/auth/callback')
def auth_callback():
    """
    Callback de Google OAuth
    """
    try:
        token = google.authorize_access_token()
        
        # Obtener información del usuario desde Google
        resp = google.get('https://www.googleapis.com/oauth2/v2/userinfo')
        user_info = resp.json()
        
        if user_info and 'email' in user_info:
            # Crear objeto usuario
            user = User(
                id=user_info.get('id', user_info.get('sub', '')),
                email=user_info['email'],
                name=user_info.get('name', 'Usuario'),
                picture=user_info.get('picture', '')
            )
            
            # Guardar información del usuario en la sesión
            session['user'] = {
                'id': user_info.get('id', user_info.get('sub', '')),
                'email': user_info['email'],
                'name': user_info.get('name', 'Usuario'),
                'picture': user_info.get('picture', '')
            }
            
            # Iniciar sesión
            login_user(user)
            print(f"✅ Usuario autenticado: {user_info['email']}")
            return redirect(url_for('index'))
        else:
            print("❌ Error: No se recibió información del usuario")
            return redirect(url_for('login'))
            
    except Exception as e:
        print(f"❌ Error en autenticación: {e}")
        import traceback
        traceback.print_exc()
        return redirect(url_for('login'))

@app.route('/logout')
@login_required
def logout():
    """
    Cerrar sesión
    """
    logout_user()
    session.pop('user', None)
    print("👋 Usuario cerró sesión")
    return redirect(url_for('login'))

# ========================================
# RUTAS DE LA APLICACIÓN
# ========================================

@app.route('/')
@login_required
def index():
    """
    Página principal con formulario de registro y lista de ventas
    """
    usuario_email = current_user.email
    estadisticas = obtener_estadisticas(usuario_email)
    # Obtener ventas activas del usuario desde BD
    ventas_db = Venta.query.filter_by(
        usuario_email=usuario_email,
        estado='Activa'
    ).order_by(Venta.fecha.desc()).all()
    ventas_activas = [v.to_dict() for v in ventas_db]
    return render_template('index.html', 
                         ventas=ventas_activas, 
                         rubros=RUBROS,
                         estadisticas=estadisticas,
                         formatear_fecha=formatear_fecha,
                         formatear_moneda=formatear_moneda,
                         datetime=datetime)

@app.route('/agregar', methods=['POST'])
@login_required
def agregar():
    """
    Ruta para agregar una nueva venta
    """
    try:
        # Obtener email del usuario actual
        usuario_email = current_user.email
        
        cliente = request.form.get('cliente', '').strip()
        valor_total = request.form.get('valor_total', 0)
        abono = request.form.get('abono', 0)
        fecha = request.form.get('fecha', '').strip()
        rubros = request.form.getlist('rubros')
        
        # Validaciones
        if not cliente:
            print("❌ Error: Cliente vacío")
            return redirect('/')
        
        # Validación obligatoria de rubros
        if not rubros:
            print("❌ Error: Debe seleccionar al menos un rubro")
            return redirect('/')
        
        try:
            valor_total = float(valor_total) if valor_total else 0
            abono = float(abono) if abono else 0
        except ValueError as e:
            print(f"❌ Error al convertir valores numéricos: {e}")
            return redirect('/')
        
        if valor_total < 0 or abono < 0:
            print("❌ Error: Valores negativos no permitidos")
            return redirect('/')
        
        if not fecha:
            fecha = datetime.now().strftime("%Y-%m-%d")
        
        nueva_venta = agregar_venta(usuario_email, cliente, valor_total, abono, rubros, fecha)
        print(f"✅ Venta agregada: ID={nueva_venta['id']}, Cliente='{nueva_venta['cliente']}', Valor=${nueva_venta['valor_total']}, Rubros: {', '.join(rubros)}")
        
        return redirect('/')
        
    except Exception as e:
        print(f"❌ Error inesperado en agregar venta: {e}")
        return redirect('/')

@app.route('/eliminar/<int:id>')
@login_required
def eliminar(id):
    """
    Ruta para eliminar una venta
    """
    usuario_email = current_user.email
    if eliminar_venta(usuario_email, id):
        print(f"🗑️ Venta {id} eliminada")
    else:
        print(f"❌ Venta {id} no encontrada")
    
    return redirect('/')

@app.route('/api/estadisticas')
@login_required
def api_estadisticas():
    """
    API para obtener estadísticas en formato JSON
    """
    usuario_email = current_user.email
    return jsonify(obtener_estadisticas(usuario_email))

@app.route('/api/ventas')
@login_required
def api_ventas():
    """
    API para obtener todas las ventas del usuario en formato JSON
    """
    usuario_email = current_user.email
    ventas_db = Venta.query.filter_by(usuario_email=usuario_email).all()
    ventas_dict = [v.to_dict() for v in ventas_db]
    return jsonify(ventas_dict)

@app.route('/pago/<int:venta_id>', methods=['GET', 'POST'])
@login_required
def gestionar_pago(venta_id):
    """
    Ruta para gestionar pagos de una venta específica
    """
    usuario_email = current_user.email
    venta = obtener_venta(usuario_email, venta_id)
    if not venta:
        return redirect('/')
    
    if request.method == 'POST':
        try:
            monto_pago = float(request.form.get('monto_pago', 0))
            tipo_pago = request.form.get('tipo_pago', 'Abono')
            
            if monto_pago <= 0:
                print("❌ Error: Monto de pago inválido")
                return redirect(f'/pago/{venta_id}')
            
            venta_actualizada = registrar_pago(usuario_email, venta_id, monto_pago, tipo_pago)
            if venta_actualizada:
                print(f"✅ Pago registrado: Venta {venta_id}, Monto: ${monto_pago}")
                if venta_actualizada['estado'] == 'Cerrada':
                    print(f"🎉 Venta {venta_id} cerrada completamente")
            else:
                print(f"❌ Error al registrar pago en venta {venta_id}")
                
        except ValueError as e:
            print(f"❌ Error de validación: {e}")
        except Exception as e:
            print(f"❌ Error inesperado: {e}")
        
        return redirect('/')
    
    # GET: Mostrar formulario de pago
    return render_template('pago.html', venta=venta, formatear_moneda=formatear_moneda, formatear_fecha=formatear_fecha)

@app.route('/historial/<int:venta_id>')
@login_required
def ver_historial(venta_id):
    """
    Ruta para ver el historial de pagos de una venta
    """
    usuario_email = current_user.email
    venta = obtener_venta(usuario_email, venta_id)
    if not venta:
        return redirect('/')
    
    return render_template('historial.html', venta=venta, formatear_moneda=formatear_moneda, formatear_fecha=formatear_fecha)

@app.route('/buscar')
@login_required
def buscar_ventas():
    """
    Ruta para buscar ventas por nombre de cliente
    """
    usuario_email = current_user.email
    query = request.args.get('q', '').strip().lower()
    
    # Obtener ventas activas del usuario desde BD
    ventas_query = Venta.query.filter_by(
        usuario_email=usuario_email,
        estado='Activa'
    )
    
    if query:
        # Filtrar por nombre de cliente que contenga la búsqueda
        ventas_query = ventas_query.filter(Venta.cliente.ilike(f'%{query}%'))
    
    ventas_db = ventas_query.order_by(Venta.fecha.desc()).all()
    ventas_filtradas = [v.to_dict() for v in ventas_db]
    
    estadisticas = obtener_estadisticas(usuario_email)
    
    return render_template('index.html', 
                         ventas=ventas_filtradas, 
                         rubros=RUBROS,
                         estadisticas=estadisticas,
                         formatear_fecha=formatear_fecha,
                         formatear_moneda=formatear_moneda,
                         datetime=datetime,
                         busqueda=query)

@app.route('/cierre-mensual', methods=['GET', 'POST'])
@login_required
def cierre_mensual():
    """
    Ruta para realizar el cierre mensual de estadísticas
    """
    usuario_email = current_user.email
    
    if request.method == 'POST':
        try:
            mes = int(request.form.get('mes', datetime.now().month))
            año = int(request.form.get('año', datetime.now().year))
            
            resumen = cerrar_mes_estadisticas(usuario_email, mes, año)
            print(f"✅ Cierre mensual realizado: {resumen['ventas_excluidas']} ventas excluidas")
            
            return redirect('/')
            
        except Exception as e:
            print(f"❌ Error en cierre mensual: {e}")
            return redirect('/')
    
    # GET: Mostrar formulario de cierre mensual
    ventas_pendientes = obtener_ventas_cerradas_pendientes(usuario_email)
    estadisticas = obtener_estadisticas(usuario_email)
    
    return render_template('cierre_mensual.html', 
                         ventas_pendientes=ventas_pendientes,
                         estadisticas=estadisticas,
                         formatear_fecha=formatear_fecha,
                         formatear_moneda=formatear_moneda,
                         datetime=datetime)

@app.route('/ventas-excluidas')
@login_required
def ventas_excluidas():
    """
    Ruta para ver las ventas excluidas de estadísticas
    """
    usuario_email = current_user.email
    ventas_excluidas_db = Venta.query.filter_by(
        usuario_email=usuario_email,
        incluida_en_estadisticas=False
    ).order_by(Venta.fecha.desc()).all()
    
    ventas_excluidas = [v.to_dict() for v in ventas_excluidas_db]
    estadisticas = obtener_estadisticas(usuario_email)
    
    return render_template('ventas_excluidas.html', 
                         ventas=ventas_excluidas,
                         estadisticas=estadisticas,
                         formatear_fecha=formatear_fecha,
                         formatear_moneda=formatear_moneda,
                         datetime=datetime)

@app.route('/estadisticas-periodo', methods=['GET', 'POST'])
@login_required
def estadisticas_periodo():
    """
    Ruta para ver estadísticas por período de tiempo
    """
    usuario_email = current_user.email
    
    if request.method == 'POST':
        fecha_inicio = request.form.get('fecha_inicio', '')
        fecha_fin = request.form.get('fecha_fin', '')
        
        if fecha_inicio and fecha_fin:
            estadisticas_periodo = obtener_estadisticas_por_periodo(usuario_email, fecha_inicio, fecha_fin)
            if estadisticas_periodo:
                return render_template('estadisticas_periodo.html',
                                     estadisticas=estadisticas_periodo,
                                     formatear_fecha=formatear_fecha,
                                     formatear_moneda=formatear_moneda,
                                     datetime=datetime,
                                     rubros=RUBROS)
            else:
                print("❌ Error al obtener estadísticas del período")
                return redirect('/estadisticas-periodo')
    
    # GET: Mostrar formulario de selección de período
    # Establecer fechas por defecto (último mes)
    fecha_fin = datetime.now().strftime("%Y-%m-%d")
    fecha_inicio = (datetime.now().replace(day=1)).strftime("%Y-%m-%d")
    
    return render_template('estadisticas_periodo.html',
                         fecha_inicio=fecha_inicio,
                         fecha_fin=fecha_fin,
                         formatear_fecha=formatear_fecha,
                         formatear_moneda=formatear_moneda,
                         datetime=datetime)

@app.route('/api/estadisticas-periodo')
@login_required
def api_estadisticas_periodo():
    """
    API para obtener estadísticas por período en formato JSON
    """
    usuario_email = current_user.email
    fecha_inicio = request.args.get('fecha_inicio', '')
    fecha_fin = request.args.get('fecha_fin', '')
    
    if fecha_inicio and fecha_fin:
        estadisticas = obtener_estadisticas_por_periodo(usuario_email, fecha_inicio, fecha_fin)
        if estadisticas:
            return jsonify(estadisticas)
    
    return jsonify({'error': 'Fechas requeridas'}), 400

@app.route('/privacy')
def privacy():
    """
    Política de privacidad - Requerida para publicar la app en Google
    """
    return render_template('privacy.html')

@app.route('/terms')
def terms():
    """
    Términos de servicio - Requerido para publicar la app en Google
    """
    return render_template('terms.html')

# ========================================
# INICIALIZACIÓN DE BASE DE DATOS
# ========================================
def init_db():
    """
    Inicializa la base de datos creando todas las tablas
    """
    with app.app_context():
        db.create_all()
        print("✅ Base de datos inicializada correctamente")

# Inicializar base de datos al cargar la aplicación (para producción con gunicorn)
with app.app_context():
    try:
        db.create_all()
        print("✅ Base de datos verificada/inicializada")
    except Exception as e:
        print(f"⚠️ Advertencia al inicializar BD: {e}")

# ========================================
# EJECUCIÓN PRINCIPAL
# ========================================

if __name__ == '__main__':
    # Inicializar base de datos al iniciar
    init_db()
    
    import socket
    
    # Obtener la IP local de la máquina
    def get_local_ip():
        try:
            # Conectar a un servidor externo para obtener la IP local
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            s.close()
            return ip
        except:
            return "127.0.0.1"
    
    # Solo ejecutar servidor Flask en desarrollo local
    # En producción (Railway, Render, etc.) se usa gunicorn según Procfile
    if os.environ.get('FLASK_ENV') != 'production':
        local_ip = get_local_ip()
        port = int(os.environ.get('PORT', 5000))
        
        print("🚀 Iniciando mi Sistema de Ventas - Carloszerpav...")
        print(f"📱 Acceso local: http://localhost:{port}")
        print(f"🌐 Acceso en red: http://{local_ip}:{port}")
        print("📱 Para acceder desde móvil/otra PC en la misma red:")
        print(f"   - Abre el navegador y ve a: http://{local_ip}:{port}")
        print("   - Asegúrate de que el firewall permita conexiones en el puerto 5000")
        print("\n✨ Características de mi sistema - Carloszerpav:")
        print("   - Registro de ventas con cliente y valor")
        print("   - Cálculo automático de saldo pendiente")
        print("   - Selección múltiple de rubros")
        print("   - Fecha automática con opción de modificación")
        print("   - Modo oscuro predeterminado")
        print("   - Interfaz moderna y responsive")
        print("   - Estadísticas por rubro")
        print("   - Formato de moneda")
        print("   - Validación de formularios")
        print("   - Sistema de pagos en cuotas")
        print("   - Historial de pagos por venta")
        print("   - Buscador por nombre de cliente")
        print("   - Cierre mensual de estadísticas")
        print("   - Gestión de ventas excluidas")
        print("📋 Mis rubros de trabajo - Carloszerpav:")
        for rubro in RUBROS:
            print(f"   - {rubro}")
        print("📁 Estructura de archivos:")
        print("   - app.py (aplicación Flask)")
        print("   - templates/index.html (plantilla)")
        print("   - static/css/style.css (estilos)")
        print("   - static/js/script.js (JavaScript)")
        print("\n💡 Para mantener la aplicación funcionando:")
        print("   - No cierres esta ventana")
        print("   - Usa el archivo 'iniciar_app.bat' para ejecutar más fácilmente")
        print("   - O ejecuta: python app.py")
        print("\n🔒 Configuración de red:")
        print(f"   - Host: 0.0.0.0 (accesible desde cualquier IP)")
        print(f"   - Puerto: {port}")
        print(f"   - IP local: {local_ip}")
        
        # Modo debug solo en desarrollo local
        debug_mode = os.environ.get('FLASK_DEBUG', 'False').lower() == 'true'
        app.run(debug=debug_mode, host='0.0.0.0', port=port)
