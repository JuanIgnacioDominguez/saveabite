import os
import datetime
import uuid
from flask import Flask, jsonify, render_template, request, redirect, url_for, flash, session
from flask_mail import Mail, Message
import sqlite3
from werkzeug.utils import secure_filename
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'your_secret_key'

# Configuración de Flask-Mail
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'saveabite.sip@gmail.com'
app.config['MAIL_PASSWORD'] = 'bduo lszu miho zdhv'
app.config['MAIL_DEFAULT_SENDER'] = 'saveabite.sip@gmail.com'

# Configuración de subida de archivos
UPLOAD_FOLDER = 'static/uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

mail = Mail(app)

def get_db_connection():
    conn = sqlite3.connect('flask_db.db')
    conn.row_factory = sqlite3.Row
    return conn

def create_tables():
    conn = get_db_connection()
    # Crear tabla usuarios
    conn.execute('''
        CREATE TABLE IF NOT EXISTS usuarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre_usuario TEXT NOT NULL,
            correo_electronico TEXT NOT NULL UNIQUE,
            contrasena TEXT NOT NULL,
            imagen TEXT,  -- Columna para almacenar imágenes
            membresia TEXT,
            tipo_dieta TEXT  -- Nueva columna para tipo de dieta
        )
    ''')
    # Crear tabla usuarioEmpresa
    conn.execute('''
        CREATE TABLE IF NOT EXISTS usuarioEmpresa (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre_usuario TEXT NOT NULL,
            correo_electronico TEXT NOT NULL UNIQUE,
            contrasena TEXT NOT NULL,
            imagen TEXT,  -- Columna para almacenar imágenes
            membresia TEXT,
            direccion_id INTEGER,
            FOREIGN KEY (direccion_id) REFERENCES direccionEmpresa (id)
        )
    ''')
    conn.execute('''
        CREATE TABLE IF NOT EXISTS direccionEmpresa (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            usuario_id INTEGER NOT NULL,
            calle TEXT NOT NULL,
            altura INTEGER NOT NULL,
            localidad TEXT NOT NULL,
            FOREIGN KEY (usuario_id) REFERENCES usuarioEmpresa (id)
        )
    ''')
    # Crear tabla Productos
    conn.execute('''
        CREATE TABLE IF NOT EXISTS Productos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            Empresa TEXT NOT NULL,
            nombre TEXT NOT NULL,
            tiempoEstimado TEXT NOT NULL,
            precio REAL NOT NULL,
            descripcion TEXT NOT NULL,
            imagen TEXT NOT NULL,
            tipoComida TEXT NOT NULL,
            tipo_dieta TEXT  -- Nueva columna para tipo de dieta
        )
    ''')
    # Crear tabla métodos de pago
    conn.execute('''
        CREATE TABLE IF NOT EXISTS metodos_pago (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            usuario_id INTEGER NOT NULL,
            tipo_metodo TEXT NOT NULL,
            tipo_tarjeta TEXT NOT NULL,
            nombre_titular TEXT NOT NULL,
            numero_tarjeta TEXT NOT NULL,
            fecha_vencimiento TEXT NOT NULL,
            codigo_seguridad TEXT NOT NULL,
            FOREIGN KEY (usuario_id) REFERENCES usuarios (id)
        )
    ''')
    # Crear tabla direcciones
    conn.execute('''
        CREATE TABLE IF NOT EXISTS direcciones (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            usuario_id INTEGER NOT NULL,
            calle TEXT NOT NULL,
            altura INTEGER NOT NULL,
            localidad TEXT NOT NULL,
            FOREIGN KEY (usuario_id) REFERENCES usuarios (id)
        )
    ''')
    # Crear tabla PasswordResetTokens
    conn.execute('''
        CREATE TABLE IF NOT EXISTS PasswordResetTokens (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            token TEXT NOT NULL,
            expiration DATETIME NOT NULL,
            FOREIGN KEY (user_id) REFERENCES usuarios (id)
        )
    ''')
    # Crear tabla registroAcciones
    conn.execute('''
        CREATE TABLE IF NOT EXISTS registroAcciones (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            usuario_id INTEGER NOT NULL,
            accion TEXT NOT NULL,
            fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (usuario_id) REFERENCES usuarios (id)
        )
    ''')

    conn.execute('''
        CREATE TABLE IF NOT EXISTS carrito (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            usuario_id INTEGER NOT NULL,
            producto_id INTEGER NOT NULL,
            cantidad INTEGER NOT NULL,
            FOREIGN KEY (usuario_id) REFERENCES usuarios (id),
            FOREIGN KEY (producto_id) REFERENCES Productos (id)
        )
    ''')
    conn.execute('''
        CREATE TABLE IF NOT EXISTS favoritos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            usuario_id INTEGER NOT NULL,
            producto_id INTEGER NOT NULL,
            FOREIGN KEY (usuario_id) REFERENCES usuarios (id),
            FOREIGN KEY (producto_id) REFERENCES Productos (id)
        )
    ''')
    conn.execute('''
        CREATE TABLE IF NOT EXISTS pedidos2 (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            usuario_id INTEGER NOT NULL,
            fecha DATE NOT NULL,
            total REAL NOT NULL,
            FOREIGN KEY (usuario_id) REFERENCES usuarios (id)
        )
    ''')
    conn.commit()
    conn.close()

def add_membership_field():
    conn = get_db_connection()
    # Añadir el campo membresia a la tabla usuarios
    try:
        conn.execute('''
            ALTER TABLE usuarios
            ADD COLUMN membresia TEXT
        ''')
    except sqlite3.OperationalError:
        # La columna ya existe
        pass
    # Añadir el campo membresia a la tabla usuarioEmpresa
    try:
        conn.execute('''
            ALTER TABLE usuarioEmpresa
            ADD COLUMN membresia TEXT
        ''')
    except sqlite3.OperationalError:
        # La columna ya existe
        pass

    try:
        conn.execute('''
            ALTER TABLE usuarios
            ADD COLUMN tipo_dieta TEXT
        ''')
    except sqlite3.OperationalError:
        # La columna ya existe
        pass

    try:
        conn.execute('''
            ALTER TABLE Productos
            ADD COLUMN tipo_dieta TEXT
        ''')
    except sqlite3.OperationalError:
        # La columna ya existe
        pass
    conn.commit()
    conn.close()

create_tables()
add_membership_field()

def generate_token():
    return str(uuid.uuid4())

def send_reset_email(email, token):
    reset_link = url_for('reset_password', token=token, _external=True)
    msg = Message('Restablecer Contraseña', recipients=[email])
    msg.body = f'Para restablecer su contraseña, haga clic en el siguiente enlace: {reset_link}'
    mail.send(msg)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def registrar_accion(usuario_id, accion):
    conn = get_db_connection()
    conn.execute('INSERT INTO registroAcciones (usuario_id, accion) VALUES (?, ?)', (usuario_id, accion))
    conn.commit()
    conn.close()

@app.route("/", methods=['GET', 'POST'])
def index():
    return render_template('index.html')

@app.route("/login", methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        conn = get_db_connection()
        user = conn.execute('SELECT * FROM usuarios WHERE correo_electronico = ? AND contrasena = ?', (email, password)).fetchone()
        vendor = conn.execute('SELECT * FROM usuarioEmpresa WHERE correo_electronico = ? AND contrasena = ?', (email, password)).fetchone()
        conn.close()
        if user:
            session['user_id'] = user['id']
            session['user_name'] = user['nombre_usuario']
            session['user_email'] = user['correo_electronico']
            session['user_image'] = user['imagen']
            return redirect(url_for('menu'))
        elif vendor:
            session['user_id'] = vendor['id']
            session['user_name'] = vendor['nombre_usuario']
            session['user_email'] = vendor['correo_electronico']
            session['user_image'] = vendor['imagen']
            return redirect(url_for('menu_empresas'))
        else:
            flash('Cuenta no encontrada o contraseña incorrecta', 'error')
            return redirect(url_for('login'))
    return render_template('general/Iniciarsesion.html')

@app.route("/register", methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        password = request.form['password']
        is_vendor = 'is_vendor' in request.form
        image = 'img/defaultuser.png'  # Ruta a la imagen predeterminada

        if not name or not email or not password:
            flash('Por favor, complete todas las casillas', 'error')
            return redirect(url_for('register'))

        conn = get_db_connection()
        try:
            if is_vendor:
                conn.execute('INSERT INTO usuarioEmpresa (nombre_usuario, correo_electronico, contrasena, imagen) VALUES (?, ?, ?, ?)', (name, email, password, image))
                conn.commit()
                vendor = conn.execute('SELECT * FROM usuarioEmpresa WHERE correo_electronico = ? AND contrasena = ?', (email, password)).fetchone()
                conn.close()
                session['user_id'] = vendor['id']
                session['user_name'] = vendor['nombre_usuario']
                session['user_image'] = vendor['imagen']
                return redirect(url_for('menu_empresas'))
            else:
                conn.execute('INSERT INTO usuarios (nombre_usuario, correo_electronico, contrasena, imagen) VALUES (?, ?, ?, ?)', (name, email, password, image))
                conn.commit()
                user = conn.execute('SELECT * FROM usuarios WHERE correo_electronico = ? AND contrasena = ?', (email, password)).fetchone()
                conn.close()
                session['user_id'] = user['id']
                session['user_name'] = user['nombre_usuario']
                session['user_image'] = user['imagen']
                return redirect(url_for('menu'))
        except sqlite3.IntegrityError:
            flash('El correo electrónico ya está registrado', 'error')
            return redirect(url_for('register'))
        finally:
            conn.close()
    return render_template('general/Iniciarsesion.html')

@app.route("/metodos_pago", methods=['GET', 'POST'])
def metodos_pago():
    user_id = session.get('user_id')
    conn = get_db_connection()
    if request.method == 'POST':
        tipo_tarjeta = request.form.get('tipo_tarjeta')
        nombre_titular = request.form.get('nombre_titular')
        numero_tarjeta = request.form.get('numero_tarjeta')
        fecha_vencimiento = request.form.get('fecha_vencimiento')
        codigo_seguridad = request.form.get('codigo_seguridad')
        
        # Validar la longitud del número de tarjeta y el código de seguridad
        if len(numero_tarjeta) != 16 or len(codigo_seguridad) != 3:
            flash('Número de tarjeta o código de seguridad no válidos', 'error')
            return redirect(url_for('metodos_pago'))

        conn.execute('''
            INSERT INTO metodos_pago (usuario_id, tipo_metodo, tipo_tarjeta, nombre_titular, numero_tarjeta, fecha_vencimiento, codigo_seguridad)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (user_id, 'Tarjeta de Crédito', tipo_tarjeta, nombre_titular, numero_tarjeta, fecha_vencimiento, codigo_seguridad))
        conn.commit()
        registrar_accion(user_id, 'Añadido método de pago')
    
    metodos_pago = conn.execute('SELECT * FROM metodos_pago WHERE usuario_id = ?', (user_id,)).fetchall()
    conn.close()
    return render_template('Perfil/MetodosPago.html', metodos_pago=metodos_pago)

@app.route("/borrar_metodo_pago/<int:id>", methods=['POST'])
def borrar_metodo_pago(id):
    user_id = session.get('user_id')
    conn = get_db_connection()
    conn.execute('DELETE FROM metodos_pago WHERE id = ?', (id,))
    conn.commit()
    conn.close()
    registrar_accion(user_id, 'Eliminado método de pago')
    return redirect(url_for('metodos_pago'))

@app.route("/direcciones", methods=['GET', 'POST'])
def direcciones():
    user_id = session.get('user_id')
    conn = get_db_connection()
    if request.method == 'POST':
        calle = request.form['calle']
        altura = request.form['altura']
        localidad = request.form['localidad']
        conn.execute('''
            INSERT INTO direcciones (usuario_id, calle, altura, localidad)
            VALUES (?, ?, ?, ?)
        ''', (user_id, calle, altura, localidad))
        conn.commit()
        registrar_accion(user_id, 'Añadida dirección')
    
    direcciones = conn.execute('SELECT * FROM direcciones WHERE usuario_id = ?', (user_id,)).fetchall()
    conn.close()
    return render_template('Perfil/Direcciones.html', direcciones=direcciones)

@app.route("/borrar_direccion/<int:id>", methods=['POST'])
def borrar_direccion(id):
    user_id = session.get('user_id')
    conn = get_db_connection()
    conn.execute('DELETE FROM direcciones WHERE id = ?', (id,))
    conn.commit()
    conn.close()
    registrar_accion(user_id, 'Eliminada dirección')
    return redirect(url_for('direcciones'))

@app.route("/forgot_password",methods=['GET', 'POST'])
def forgot_password():
    email = request.form['email']
    conn = get_db_connection()
    user = conn.execute('SELECT * FROM usuarios WHERE correo_electronico = ?', (email,)).fetchone()
    if user:
        # Generar un token y almacenarlo en la base de datos
        token = generate_token()
        expiration = datetime.datetime.now() + datetime.timedelta(hours=1)
        conn.execute('INSERT INTO PasswordResetTokens (user_id, token, expiration) VALUES (?, ?, ?)', (user['id'], token, expiration))
        conn.commit()
        # Enviar un correo electrónico con el enlace de restablecimiento
        send_reset_email(email, token)
        registrar_accion(user['id'], 'Solicitud de restablecimiento de contraseña')
        flash('Se ha enviado un enlace para restablecer la contraseña a su email', 'success')
    else:
        flash('Correo electrónico no encontrado', 'error')
    conn.close()
    return redirect(url_for('login'))

@app.route("/estadistica", methods=['GET'])
def estadistica():
    # Add your logic to handle the resumen_empresa page here
    return render_template('perfiles_empresa/estadistica.html')

@app.route("/reset_password/<token>", methods=['GET', 'POST'])
def reset_password(token):
    conn = get_db_connection()
    token_data = conn.execute('SELECT * FROM PasswordResetTokens WHERE token = ?', (token,)).fetchone()
    
    if not token_data:
        flash('El token ha expirado o no es válido', 'error')
        conn.close()
        return redirect(url_for('forgot_password'))
    
    try:
        expiration = datetime.datetime.strptime(token_data['expiration'], '%Y-%m-%d %H:%M:%S.%f')
    except ValueError:
        expiration = datetime.datetime.strptime(token_data['expiration'], '%Y-%m-%d %H:%M:%S')
    
    if expiration < datetime.datetime.now():
        flash('El token ha expirado o no es válido', 'error')
        conn.close()
        return redirect(url_for('forgot_password'))

    if request.method == 'POST':
        new_password = request.form['password']
        user_id = token_data['user_id']
        conn.execute('UPDATE usuarios SET contrasena = ? WHERE id = ?', (new_password, user_id))
        conn.execute('DELETE FROM PasswordResetTokens WHERE user_id = ?', (user_id,))
        conn.commit()
        registrar_accion(user_id, 'Restablecimiento de contraseña')
        flash('Contraseña actualizada con éxito', 'success')
        conn.close()
        return redirect(url_for('login'))

    conn.close()
    return render_template('general/reset_password.html', token=token)


@app.route('/membresia', methods=['GET', 'POST'])
def membresia():
    user_id = session.get('user_id')
    conn = get_db_connection()
    user = conn.execute('SELECT * FROM usuarios WHERE id = ?', (user_id,)).fetchone()
    membresia = user['membresia'] if user else None
    metodos_pago = conn.execute('SELECT * FROM metodos_pago WHERE usuario_id = ?', (user_id,)).fetchall()
    conn.close()
    return render_template('Perfil/Membresia.html', membresia=membresia, metodos_pago=metodos_pago)

@app.route('/seleccionar_membresia/<membresia>', methods=['POST'])
def seleccionar_membresia(membresia):
    user_id = session.get('user_id')
    metodo_pago_id = request.form['payment_method']

    # Obtener información del método de pago seleccionado
    conn = get_db_connection()
    metodo_pago = conn.execute('SELECT * FROM metodos_pago WHERE id = ? AND usuario_id = ?', (metodo_pago_id, user_id)).fetchone()
    if metodo_pago:
        # Lógica de procesamiento de pago aquí...
        # Actualizar la membresía del usuario
        conn.execute('UPDATE usuarios SET membresia = ? WHERE id = ?', (membresia, user_id))
        conn.commit()
        registrar_accion(user_id, f'Seleccionada membresía {membresia} con método de pago {metodo_pago["tipo_tarjeta"]}: **** **** **** {metodo_pago["numero_tarjeta"][-4:]}')
        flash('Membresía seleccionada con éxito', 'success')
    else:
        flash('Método de pago no válido', 'error')

    conn.close()
    return redirect(url_for('membresia'))

@app.route('/cancelar_membresia', methods=['POST'])
def cancelar_membresia():
    user_id = session.get('user_id')
    conn = get_db_connection()
    conn.execute('UPDATE usuarios SET membresia = NULL WHERE id = ?', (user_id,))
    conn.commit()
    registrar_accion(user_id, 'Cancelada membresía')
    conn.close()
    flash('Membresía dada de baja correctamente.', 'success')
    return redirect(url_for('membresia'))

@app.route('/membresia_empresa', methods=['GET', 'POST'])
def membresia_empresa():
    user_id = session.get('user_id')
    conn = get_db_connection()
    user = conn.execute('SELECT * FROM usuarioEmpresa WHERE id = ?', (user_id,)).fetchone()
    print(f'Usuario empresa encontrado: {user}')
    if user:
        membresia = user['membresia']
        print(f'Membresía encontrada: {membresia}')
    else:
        membresia = None
        print('No se encontró membresía para la empresa.')
    conn.close()
    return render_template('perfiles_empresa/MembresiaEmpresa.html', membresia=membresia)

@app.route('/seleccionar_membresia_empresa/<empresa_membresia>', methods=['POST'])
def seleccionar_membresia_empresa(empresa_membresia):
    user_id = session.get('user_id')
    conn = get_db_connection()
    conn.execute('UPDATE usuarioEmpresa SET membresia = ? WHERE id = ?', (empresa_membresia, user_id))
    conn.commit()
    registrar_accion(user_id, 'Seleccionada membresía de empresa')
    conn.close()
    flash('Membresía seleccionada con éxito', 'success')
    return '', 204

@app.route('/cancelar_membresia_empresa', methods=['POST'])
def cancelar_membresia_empresa():
    user_id = session.get('user_id')
    conn = get_db_connection()
    conn.execute('UPDATE usuarioEmpresa SET membresia = NULL WHERE id = ?', (user_id,))
    conn.commit()
    registrar_accion(user_id, 'Cancelada membresía de empresa')
    conn.close()
    flash('Membresía de empresa dada de baja correctamente.', 'success')
    return redirect(url_for('membresia_empresa'))

@app.route("/menu", methods=['GET'])
def menu():
    user_name = session.get('user_name')
    user_image = session.get('user_image')
    user_id = session.get('user_id')
    query = request.args.get('query', '').lower()
    conn = get_db_connection()
    
    # Obtener el tipo de dieta del usuario
    user = conn.execute('SELECT tipo_dieta FROM usuarios WHERE id = ?', (user_id,)).fetchone()
    tipo_dieta = user['tipo_dieta'] if user else None

    # Actualizar la consulta para unir usuarioEmpresa con direccionEmpresa
    restaurantes = conn.execute('''
        SELECT usuarioEmpresa.id, usuarioEmpresa.nombre_usuario, usuarioEmpresa.imagen,
            direccionEmpresa.calle, direccionEmpresa.altura, direccionEmpresa.localidad
        FROM usuarioEmpresa
        LEFT JOIN direccionEmpresa ON usuarioEmpresa.id = direccionEmpresa.usuario_id
    ''').fetchall()
    
    if query:
        productos = conn.execute('''
            SELECT * FROM Productos
            WHERE LOWER(nombre) LIKE ?
            OR LOWER(descripcion) LIKE ?
            OR LOWER(tipoComida) LIKE ?
        ''', (f'%{query}%', f'%{query}%', f'%{query}%')).fetchall()
    else:
        productos = conn.execute('SELECT * FROM Productos').fetchall()
    
    recomendados = []
    if tipo_dieta:
        recomendados = conn.execute('''
            SELECT * FROM Productos
            WHERE LOWER(tipo_dieta) = ?
            LIMIT 6
        ''', (tipo_dieta.lower(),)).fetchall()
    
    conn.close()
    return render_template('general/menu.html', user_name=user_name, user_image=user_image, productos=productos, recomendados=recomendados, tipo_dieta=tipo_dieta, restaurantes=restaurantes)


@app.route('/filter_menu', methods=['GET'])
def filter_menu():
    user_name = session.get('user_name')
    user_image = session.get('user_image')
    tipo_comida = request.args.get('tipoComida', 'todos')
    
    conn = get_db_connection()
    if tipo_comida == 'todos':
        productos = get_all_productos(conn)
    else:
        productos = get_productos_by_tipo(conn, tipo_comida)
    conn.close()
    
    return render_template('general/menu.html', user_name=user_name, user_image=user_image, productos=productos, tipo_comida=tipo_comida)

def get_all_productos(conn):
    return conn.execute('SELECT * FROM Productos').fetchall()

def get_productos_by_tipo(conn, tipo):
    return conn.execute('SELECT * FROM Productos WHERE tipoComida = ?', (tipo,)).fetchall()

@app.route("/pedidos", methods=['GET'])
def pedidos():
    pedidos = [
        {
            'date': '2024-06-18',
            'restaurant': 'Restaurante 1',
            'price': 100.0
        },
        {
            'date': '2024-06-19',
            'restaurant': 'Restaurante 2',
            'price': 200.0
        },
        {
            'date': '2024-06-20',
            'restaurant': 'Restaurante 3',
            'price': 300.0
        }
    ]
    return render_template('general/pedidos.html', pedidos=pedidos)

@app.route("/pedidos_cliente")
def pedidos_cliente():
    user_id = session.get('user_id')
    conn = get_db_connection()
    cursor = conn.cursor()

    pedidos = cursor.execute('''
        SELECT id, fecha, total
        FROM pedidos2
        WHERE usuario_id = ?
        ORDER BY fecha DESC
    ''', (user_id,)).fetchall()

    conn.close()

    return render_template('general/pedidosCliente.html', pedidos=pedidos)

@app.route("/informacion", methods=['GET'])
def informacion():
    return render_template('general/informacionEmpresas.html')

@app.route("/informacionUsuario", methods=['GET'])
def informacionUsuario():
    return render_template('general/informacionUsuario.html')

@app.route("/perfil_usuario", methods=['GET', 'POST'])
def perfil_usuario():
    user = {'name': session.get('user_name'), 'email': session.get('user_email'), 'image': session.get('user_image')}
    return render_template('Perfil/PerfilUsuario.html', user=user)

@app.route("/menu_empresas", methods=['GET'])
def menu_empresas():
    restaurant = {
        "name": session.get('user_name'),
        "address": "Dirección del Restaurante",
        "email": session.get('user_email'),
        "image": session.get('user_image')
    }
    return render_template('general/menu_empresas.html', restaurant=restaurant)

@app.route('/editar_perfil', methods=['GET', 'POST'])
def editar_perfil():
    user_id = session.get('user_id')
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        tipo_dieta = request.form['tipo_dieta']
        conn = get_db_connection()
        conn.execute('UPDATE usuarios SET nombre_usuario = ?, correo_electronico = ?, tipo_dieta = ? WHERE id = ?', (name, email, tipo_dieta, user_id))
        conn.commit()
        registrar_accion(user_id, 'Editado perfil')
        conn.close()
        session['user_name'] = name
        session['user_email'] = email
        flash('Perfil actualizado con éxito', 'success')
        return redirect(url_for('perfil_usuario'))
    
    conn = get_db_connection()
    user = conn.execute('SELECT nombre_usuario, correo_electronico, tipo_dieta FROM usuarios WHERE id = ?', (user_id,)).fetchone()
    conn.close()
    if user:
        user_data = {
            'name': user['nombre_usuario'],
            'email': user['correo_electronico'],
            'tipo_dieta': user['tipo_dieta']
        }
    else:
        user_data = {}
    
    return render_template('Perfil/EditarPerfil.html', user=user_data)


@app.route("/soporte")
def soporte():
    return render_template('Perfil/Soporte.html')

@app.route("/perfil_empresa", methods=['GET', 'POST'])
def perfil_empresa():
    company = {'name': session.get('user_name'), 'email': session.get('user_email'), 'image': session.get('user_image')}
    return render_template('perfiles_empresa/PerfilEmpresa.html', company=company)

@app.route("/direcciones_empresa", methods=['GET', 'POST'])
def direcciones_empresa():
    user_id = session.get('user_id')
    conn = get_db_connection()
    
    if request.method == 'POST':
        calle = request.form['calle']
        altura = request.form['altura']
        localidad = request.form['localidad']
        
        # Verificar si ya existe una dirección para este usuario
        existing_address = conn.execute('SELECT * FROM direccionEmpresa WHERE usuario_id = ?', (user_id,)).fetchone()
        if existing_address:
            # Actualizar la dirección existente
            conn.execute('UPDATE direccionEmpresa SET calle = ?, altura = ?, localidad = ? WHERE usuario_id = ?', (calle, altura, localidad, user_id))
        else:
            # Insertar una nueva dirección
            conn.execute('''
                INSERT INTO direccionEmpresa (usuario_id, calle, altura, localidad)
                VALUES (?, ?, ?, ?)
            ''', (user_id, calle, altura, localidad))
        
        conn.commit()
        registrar_accion(user_id, 'Añadida o actualizada dirección')
    
    direccion = conn.execute('SELECT * FROM direccionEmpresa WHERE usuario_id = ?', (user_id,)).fetchone()
    conn.close()
    return render_template('perfiles_empresa/DireccionesEmpresa.html', direccion=direccion)

@app.route('/delete_direccionEmpresa/<int:id>', methods=['POST'])
def delete_direccionEmpresa(id):
    user_id = session.get('user_id')
    conn = get_db_connection()
    conn.execute('DELETE FROM direccionEmpresa WHERE id = ? AND usuario_id = ?', (id, user_id))
    conn.commit()
    conn.close()
    registrar_accion(user_id, 'Eliminada dirección')
    return redirect(url_for('direcciones_empresa'))

@app.route("/editar_perfil_empresa", methods=['GET', 'POST'])
def editar_perfil_empresa():
    user_id = session.get('user_id')
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        conn = get_db_connection()
        conn.execute('UPDATE usuarioEmpresa SET nombre_usuario = ?, correo_electronico = ? WHERE id = ?', (name, email, user_id))
        conn.commit()
        registrar_accion(user_id, 'Editado perfil de empresa')
        conn.close()
        session['user_name'] = name
        session['user_email'] = email
        flash('Perfil de empresa actualizado con éxito', 'success')
        return redirect(url_for('perfil_empresa'))
    company = {'name': session.get('user_name'), 'email': session.get('user_email')}
    return render_template('perfiles_empresa/EditarPerfilEmpresa.html', company=company)


@app.route("/soporte_empresa")
def soporte_empresa():
    return render_template('perfiles_empresa/SoporteEmpresa.html')

# Nuevo endpoint para 'favoritos'
@app.route("/favoritos", methods=['GET'])
def favoritos():
    user_id = session.get('user_id')
    conn = get_db_connection()
    fav_item = conn.execute('''
        SELECT p.* FROM Productos p
        JOIN favoritos f ON p.id = f.producto_id
        WHERE f.usuario_id = ?
    ''', (user_id,)).fetchall()
    conn.close()
    return render_template('general/favoritos.html', fav_item=fav_item)

# Endpoint para subir imágenes
@app.route('/upload_image', methods=['POST'])
def upload_image():
    if 'profile_image' not in request.files:
        flash('No file part', 'error')
        return redirect(url_for('perfil_usuario'))
    file = request.files['profile_image']
    if file.filename == '':
        flash('No selected file', 'error')
        return redirect(url_for('perfil_usuario'))
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        
        # Crear directorio si no existe
        os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
        
        file.save(file_path)
        
        # Actualizar la imagen del usuario en la base de datos
        user_id = session.get('user_id')
        conn = get_db_connection()
        conn.execute('UPDATE usuarios SET imagen = ? WHERE id = ?', (filename, user_id))
        conn.commit()
        registrar_accion(user_id, 'Actualizada imagen de perfil')
        conn.close()
        
        # Actualizar la sesión con la nueva imagen
        session['user_image'] = filename
        
        flash('Imagen de perfil actualizada con éxito', 'success')
        return redirect(url_for('perfil_usuario'))
    else:
        flash('Tipo de archivo no permitido', 'error')
        return redirect(url_for('perfil_usuario'))
    
@app.route('/upload_imageEmpresa', methods=['POST'])
def upload_imageEmpresa():
    if 'profile_image' not in request.files:
        flash('No file part', 'error')
        return redirect(url_for('perfil_empresa'))
    file = request.files['profile_image']
    if file.filename == '':
        flash('No selected file', 'error')
        return redirect(url_for('perfil_empresa'))
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        
        # Crear directorio si no existe
        os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
        
        file.save(file_path)
        
        # Actualizar la imagen del usuario en la base de datos
        user_id = session.get('user_id')
        conn = get_db_connection()
        conn.execute('UPDATE usuarioEmpresa SET imagen = ? WHERE id = ?', (filename, user_id))
        conn.commit()
        registrar_accion(user_id, 'Actualizada imagen de perfil')
        conn.close()
        
        # Actualizar la sesión con la nueva imagen
        session['user_image'] = filename
        
        flash('Imagen de perfil actualizada con éxito', 'success')
        return redirect(url_for('perfil_empresa'))
    else:
        flash('Tipo de archivo no permitido', 'error')
        return redirect(url_for('perfil_empresa'))

@app.route("/ver_comidas", methods=['GET'])
def VerComidas():
    conn = get_db_connection()
    comidas = conn.execute('SELECT * FROM Productos').fetchall()
    conn.close()
    return render_template('general/VerComidas.html', comidas=comidas)

@app.route("/producto/<int:id>", methods=['GET'])
def producto(id):
    conn = get_db_connection()
    producto = conn.execute('SELECT * FROM Productos WHERE id = ?', (id,)).fetchone()
    conn.close()
    if producto is None:
        flash('Producto no encontrado', 'error')
        return redirect(url_for('VerComidas'))
    return render_template('general/Producto.html', producto=producto)

@app.route("/crear_producto", methods=['GET', 'POST'])
def crear_producto():
    if request.method == 'POST':
        nombre = request.form['nombre']
        precio = request.form['precio']
        descripcion = request.form['descripcion']
        categoria = request.form['categoria']
        tipo_dieta = request.form['tipo_dieta']
        file = request.files['imagen']
        
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            
            # Crear directorio si no existe
            os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
            
            file.save(file_path)
            
            # Guardar el producto en la base de datos
            conn = get_db_connection()
            conn.execute('''
                INSERT INTO Productos (Empresa, nombre, tiempoEstimado, precio, descripcion, imagen, tipoComida, tipo_dieta) 
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (session.get('user_name'), nombre, '30 min', precio, descripcion, filename, categoria, tipo_dieta))
            conn.commit()
            conn.close()
            
            flash('Producto creado con éxito', 'success')
            return redirect(url_for('menu_empresas'))
        
    return render_template('crear_producto/CrearProducto.html')

@app.route('/logout', methods=['POST'])
def logout():
    session.clear()
    return redirect(url_for("index"))

# Endpoint para subir imágenes de la empresa
@app.route('/upload_company_image', methods=['POST'])
def upload_company_image():
    if 'company_image' not in request.files:
        flash('No file part', 'error')
        return redirect(url_for('perfil_empresa'))
    file = request.files['company_image']
    if file.filename == '':
        flash('No selected file', 'error')
        return redirect(url_for('perfil_empresa'))
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        
        # Crear directorio si no existe
        os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
        
        file.save(file_path)
        
        # Actualizar la imagen de la empresa en la base de datos
        user_id = session.get('user_id')
        conn = get_db_connection()
        conn.execute('UPDATE usuarioEmpresa SET imagen = ? WHERE id = ?', (filename, user_id))
        conn.commit()
        registrar_accion(user_id, 'Actualizada imagen de la empresa')
        conn.close()
        
        # Actualizar la sesión con la nueva imagen
        session['user_image'] = filename
        
        flash('Imagen de la empresa actualizada con éxito', 'success')
        return redirect(url_for('perfil_empresa'))
    else:
        flash('Tipo de archivo no permitido', 'error')
        return redirect(url_for('perfil_empresa'))
    
@app.route("/guardar_perfil", methods=['POST'])
def guardar_perfil():
    user_id = session.get('user_id')
    nombre = request.form['name']
    correo_electronico = request.form['email']
    nueva_contrasena = request.form.get('new_password', None)

    conn = get_db_connection()
    user = conn.execute('SELECT * FROM usuarios WHERE id = ?', (user_id,)).fetchone()

    cambios = []
    if user['nombre_usuario'] != nombre:
        cambios.append('Nombre cambiado de {} a {}'.format(user['nombre_usuario'], nombre))
        conn.execute('UPDATE usuarios SET nombre_usuario = ? WHERE id = ?', (nombre, user_id))
    if user['correo_electronico'] != correo_electronico:
        cambios.append('Correo electrónico cambiado de {} a {}'.format(user['correo_electronico'], correo_electronico))
        conn.execute('UPDATE usuarios SET correo_electronico = ? WHERE id = ?', (correo_electronico, user_id))
    if nueva_contrasena and user['contrasena'] != nueva_contrasena:
        cambios.append('Contraseña cambiada')
        conn.execute('UPDATE usuarios SET contrasena = ? WHERE id = ?', (nueva_contrasena, user_id))

    conn.commit()
    conn.close()

    for cambio in cambios:
        registrar_accion(user_id, cambio)

    flash('Perfil actualizado con éxito', 'success')
    return redirect(url_for('perfil_usuario'))

@app.route("/carrito", methods=['GET'])
def carrito():
    user_id = session.get('user_id')
    conn = get_db_connection()
    carrito_items = conn.execute('''
        SELECT Productos.id, Productos.nombre, Productos.precio, Productos.imagen, carrito.cantidad
        FROM carrito
        JOIN Productos ON carrito.producto_id = Productos.id
        WHERE carrito.usuario_id = ?
    ''', (user_id,)).fetchall()
    conn.close()
    return render_template('carrito/Carrito2.html', carrito_items=carrito_items)

@app.route("/agregar_al_carrito/<int:producto_id>", methods=['POST'])
def agregar_al_carrito(producto_id):
    user_id = session.get('user_id')
    cantidad = request.form.get('cantidad', type=int)  # Obtiene la cantidad del formulario y la convierte a entero
    if not cantidad or cantidad < 1:
        cantidad = 1  # Asegura que la cantidad sea al menos 1 si no se proporciona o es inválida

    conn = get_db_connection()
    item = conn.execute('SELECT * FROM carrito WHERE usuario_id = ? AND producto_id = ?', (user_id, producto_id)).fetchone()
    
    if item:
        # Actualiza la cantidad del producto en el carrito con la cantidad especificada
        conn.execute('UPDATE carrito SET cantidad = cantidad + ? WHERE usuario_id = ? AND producto_id = ?', (cantidad, user_id, producto_id))
    else:
        # Agrega el producto al carrito con la cantidad especificada
        conn.execute('INSERT INTO carrito (usuario_id, producto_id, cantidad) VALUES (?, ?, ?)', (user_id, producto_id, cantidad))
    
    conn.commit()
    conn.close()
    flash('Producto agregado al carrito', 'success')
    return redirect(url_for('menu', id=producto_id))

@app.route("/agregar_al_carrito1/<int:producto_id>", methods=['POST'])
def agregar_al_carrito1(producto_id):
    return redirect(url_for('producto', id=producto_id))

@app.route("/eliminar_del_carrito/<int:producto_id>", methods=['POST'])
def eliminar_del_carrito(producto_id):
    user_id = session.get('user_id')
    conn = get_db_connection()
    conn.execute('DELETE FROM carrito WHERE usuario_id = ? AND producto_id = ?', (user_id, producto_id))
    conn.commit()
    conn.close()
    flash('Producto eliminado del carrito', 'success')
    return redirect(url_for('carrito'))

@app.route("/agregar_a_favoritos/<int:producto_id>", methods=['POST'])
def agregar_a_favoritos(producto_id):
    user_id = session.get('user_id')
    conn = get_db_connection()
    # Verifica si el producto ya está en favoritos para el usuario
    item = conn.execute('SELECT * FROM favoritos WHERE usuario_id = ? AND producto_id = ?', (user_id, producto_id)).fetchone()
    
    if item is None:  # Si el producto no está en favoritos, lo agrega
        conn.execute('INSERT INTO favoritos (usuario_id, producto_id) VALUES (?, ?)', (user_id, producto_id))
        flash('Producto agregado a favoritos', 'success')
    else:  # Si el producto ya está en favoritos, muestra un mensaje
        flash('Producto ya está en favoritos', 'error')
    
    conn.commit()
    conn.close()
    return redirect(url_for('producto', id=producto_id))

@app.route("/eliminar_de_favoritos/<int:producto_id>", methods=['POST'])
def eliminar_de_favoritos (producto_id):
    user_id = session.get('user_id')
    conn = get_db_connection()
    conn.execute('DELETE FROM favoritos WHERE usuario_id = ? AND producto_id = ?', (user_id, producto_id))
    conn.commit()
    conn.close()
    flash('Producto eliminado de favoritos', 'success')
    return redirect(url_for('favoritos'))

@app.route("/confirmar_compra", methods=['POST'])
def confirmar_compra():
    user_id = session.get('user_id')  # Asegúrate de que el user_id está correctamente establecido en la sesión
    if not user_id:
        # Considera redirigir al usuario a la página de inicio de sesión si user_id no está en la sesión
        return redirect(url_for('login'))

    conn = get_db_connection()
    cursor = conn.cursor()

    carrito_items = cursor.execute('SELECT * FROM carrito WHERE usuario_id = ?', (user_id,)).fetchall()

    total = 0
    for item in carrito_items:
        producto = cursor.execute('SELECT precio FROM Productos WHERE id = ?', (item['producto_id'],)).fetchone()
        if producto:
            total += item['cantidad'] * producto['precio']

    ahora = datetime.now().date()

    cursor.execute('''
        INSERT INTO pedidos2 (usuario_id, fecha, total)
        VALUES (?, ?, ?)
    ''', (user_id, ahora, total))

    cursor.execute('DELETE FROM carrito WHERE usuario_id = ?', (user_id,))

    conn.commit()
    conn.close()

    return redirect(url_for('pedidos_cliente'))

if __name__ == "__main__":
    app.run(debug=True)
