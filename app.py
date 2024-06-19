import os
import datetime
import uuid
from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_mail import Mail, Message
import sqlite3
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = 'your_secret_key'

# Configuración de Flask-Mail
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'saveabite.sip@gmail.com'
app.config['MAIL_PASSWORD'] = 'bduo lszu miho zdhv'
app.config['MAIL_DEFAULT_SENDER'] = 'saveabite.sip@gmail.com'

mail = Mail(app)

# Configuración de subida de archivos
UPLOAD_FOLDER = 'static/uploads/'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def get_db_connection():
    conn = sqlite3.connect('flask_db.db')
    conn.row_factory = sqlite3.Row
    return conn

def create_tables():
    conn = get_db_connection()
    conn.execute('''
        CREATE TABLE IF NOT EXISTS usuarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre_usuario TEXT NOT NULL,
            correo_electronico TEXT NOT NULL UNIQUE,
            contrasena TEXT NOT NULL,
            imagen TEXT,
            membresia TEXT
        )
    ''')
    conn.execute('''
        CREATE TABLE IF NOT EXISTS usuarioEmpresa (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre_usuario TEXT NOT NULL,
            correo_electronico TEXT NOT NULL UNIQUE,
            contrasena TEXT NOT NULL,
            imagen TEXT,
            membresia TEXT 
        )
    ''')
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
            cantidadPersonas INTEGER NOT NULL
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
        CREATE TABLE IF NOT EXISTS carrito (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            usuario_id INTEGER NOT NULL,
            producto_id INTEGER NOT NULL,
            FOREIGN KEY (usuario_id) REFERENCES usuarios (id),
            FOREIGN KEY (producto_id) REFERENCES Productos (id)
        )
    ''')
    conn.execute('''
        CREATE TABLE IF NOT EXISTS metodos_pago (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            usuario_id INTEGER NOT NULL,
            tipo_metodo TEXT NOT NULL,
            tipo_tarjeta TEXT,
            numero_tarjeta TEXT,
            FOREIGN KEY (usuario_id) REFERENCES usuarios (id)
        )
    ''')
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
    conn.execute('''
        CREATE TABLE IF NOT EXISTS PasswordResetTokens (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            token TEXT NOT NULL,
            expiration DATETIME NOT NULL,
            FOREIGN KEY (user_id) REFERENCES usuarios (id)
        )
    ''')
    conn.commit()
    conn.close()

create_tables()

def generate_token():
    return str(uuid.uuid4())

def send_reset_email(email, token):
    reset_link = url_for('reset_password', token=token, _external=True)
    msg = Message('Restablecer Contraseña', recipients=[email])
    msg.body = f'Para restablecer su contraseña, haga clic en el siguiente enlace: {reset_link}'
    mail.send(msg)

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
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        
        conn = get_db_connection()
        user_id = session['user_id']
        conn.execute('UPDATE usuarios SET imagen = ? WHERE id = ?', (filepath, user_id))
        conn.commit()
        conn.close()

        session['user_image'] = filepath  # Update session with new image path
        flash('Image uploaded successfully', 'success')
        return redirect(url_for('perfil_usuario'))

@app.route('/upload_company_image', methods=['POST'])
def upload_company_image():
    if 'profile_image' not in request.files:
        flash('No file part', 'error')
        return redirect(url_for('perfil_empresa'))
    file = request.files['profile_image']
    if file.filename == '':
        flash('No selected file', 'error')
        return redirect(url_for('perfil_empresa'))
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        
        conn = get_db_connection()
        company_id = session['user_id']
        conn.execute('UPDATE usuarioEmpresa SET imagen = ? WHERE id = ?', (filepath, company_id))
        conn.commit()
        conn.close()

        session['user_image'] = filepath  # Update session with new image path
        flash('Image uploaded successfully', 'success')
        return redirect(url_for('perfil_empresa'))

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

@app.route("/", methods=['GET', 'POST'])
def index():
    return render_template('index.html')

@app.route("/login", methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        conn = get_db_connection()
        user = conn.execute('SELECT * FROM usuarios WHERE correo_electronico = ?', (email,)).fetchone()
        vendor = conn.execute('SELECT * FROM usuarioEmpresa WHERE correo_electronico = ?', (email,)).fetchone()
        conn.close()
        if user and check_password_hash(user['contrasena'], password):
            session['user_id'] = user['id']
            session['user_name'] = user['nombre_usuario']
            session['user_email'] = user['correo_electronico']
            session['user_image'] = user['imagen']
            return redirect(url_for('menu'))
        elif vendor and check_password_hash(vendor['contrasena'], password):
            session['user_id'] = vendor['id']
            session['user_name'] = vendor['nombre_usuario']
            session['user_email'] = vendor['correo_electronico']
            session['user_image'] = vendor['imagen']
            return redirect(url_for('menu_restaurant'))
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
        image = 'static/img/defaultUser.png'  # Ruta a la imagen predeterminada
        hashed_password = generate_password_hash(password)

        if not name or not email or not password:
            flash('Por favor, complete todas las casillas', 'error')
            return redirect(url_for('register'))

        conn = get_db_connection()
        try:
            if is_vendor:
                conn.execute('INSERT INTO usuarioEmpresa (nombre_usuario, correo_electronico, contrasena, imagen) VALUES (?, ?, ?, ?)', (name, email, hashed_password, image))
                conn.commit()
                vendor = conn.execute('SELECT * FROM usuarioEmpresa WHERE correo_electronico = ?', (email,)).fetchone()
                conn.close()
                session['user_id'] = vendor['id']
                session['user_name'] = vendor['nombre_usuario']
                session['user_image'] = vendor['imagen']
                return redirect(url_for('menu_restaurant'))
            else:
                conn.execute('INSERT INTO usuarios (nombre_usuario, correo_electronico, contrasena, imagen) VALUES (?, ?, ?, ?)', (name, email, hashed_password, image))
                conn.commit()
                user = conn.execute('SELECT * FROM usuarios WHERE correo_electronico = ?', (email,)).fetchone()
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
        tipo_metodo = request.form['tipo_metodo']
        tipo_tarjeta = request.form.get('tipo_tarjeta')
        numero_tarjeta = request.form.get('numero_tarjeta')
        conn.execute('''
            INSERT INTO metodos_pago (usuario_id, tipo_metodo, tipo_tarjeta, numero_tarjeta)
            VALUES (?, ?, ?, ?)
        ''', (user_id, tipo_metodo, tipo_tarjeta, numero_tarjeta))
        conn.commit()
    
    metodos_pago = conn.execute('SELECT * FROM metodos_pago WHERE usuario_id = ?', (user_id,)).fetchall()
    conn.close()
    return render_template('Perfil/MetodosPago.html', metodos_pago=metodos_pago)

@app.route("/borrar_metodo_pago/<int:id>", methods=['POST'])
def borrar_metodo_pago(id):
    conn = get_db_connection()
    conn.execute('DELETE FROM metodos_pago WHERE id = ?', (id,))
    conn.commit()
    conn.close()
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
    
    direcciones = conn.execute('SELECT * FROM direcciones WHERE usuario_id = ?', (user_id,)).fetchall()
    conn.close()
    return render_template('Perfil/Direcciones.html', direcciones=direcciones)

@app.route("/borrar_direccion/<int:id>", methods=['POST'])
def borrar_direccion(id):
    conn = get_db_connection()
    conn.execute('DELETE FROM direcciones WHERE id = ?', (id,))
    conn.commit()
    conn.close()
    return redirect(url_for('direcciones'))

@app.route("/forgot_password", methods=['POST'])
def forgot_password():
    email = request.form['email']
    conn = get_db_connection()
    user = conn.execute('SELECT * FROM usuarios WHERE correo_electronico = ?', (email,)).fetchone()
    if user:
        token = generate_token()
        expiration = datetime.datetime.now() + datetime.timedelta(hours=1)
        conn.execute('INSERT INTO PasswordResetTokens (user_id, token, expiration) VALUES (?, ?, ?)', (user['id'], token, expiration))
        conn.commit()
        send_reset_email(email, token)
        flash('Se ha enviado un enlace para restablecer la contraseña a su email', 'success')
    else:
        flash('Correo electrónico no encontrado', 'error')
    conn.close()
    return redirect(url_for('login'))

@app.route("/reset_password/<token>", methods=['GET', 'POST'])
def reset_password(token):
    conn = get_db_connection()
    token_data = conn.execute('SELECT * FROM PasswordResetTokens WHERE token = ?', (token,)).fetchone()
    if not token_data or token_data['expiration'] < datetime.datetime.now():
        flash('El token ha expirado o no es válido', 'error')
        conn.close()
        return redirect(url_for('forgot_password'))

    if request.method == 'POST':
        new_password = request.form['password']
        hashed_password = generate_password_hash(new_password)
        user_id = token_data['user_id']
        conn.execute('UPDATE usuarios SET contrasena = ? WHERE id = ?', (hashed_password, user_id))
        conn.execute('DELETE FROM PasswordResetTokens WHERE user_id = ?', (user_id,))
        conn.commit()
        flash('Contraseña actualizada con éxito', 'success')
        conn.close()
        return redirect(url_for('login'))

    conn.close()
    return render_template('reset_password.html', token=token)

@app.route('/membresia', methods=['GET', 'POST'])
def membresia():
    user_id = session.get('user_id')
    conn = get_db_connection()
    user = conn.execute('SELECT * FROM usuarios WHERE id = ?', (user_id,)).fetchone()
    membresia = user['membresia'] if user else None
    conn.close()
    return render_template('Perfil/Membresia.html', membresia=membresia)

@app.route('/seleccionar_membresia/<membresia>', methods=['POST'])
def seleccionar_membresia(membresia):
    user_id = session.get('user_id')
    conn = get_db_connection()
    conn.execute('UPDATE usuarios SET membresia = ? WHERE id = ?', (membresia, user_id))
    conn.commit()
    conn.close()
    flash('Membresía seleccionada con éxito', 'success')
    return '', 204

@app.route("/menu", methods=['GET'])
def menu():
    conn = get_db_connection()
    productos = conn.execute('SELECT * FROM Productos').fetchall()
    conn.close()
    return render_template('menu.html', productos=productos)

@app.route("/producto", methods=['GET'])
def producto():
    producto_id = request.args.get('producto_id')
    conn = get_db_connection()
    producto = conn.execute('SELECT * FROM Productos WHERE id = ?', (producto_id,)).fetchone()
    conn.close()
    return render_template('Producto.html', producto=producto)

@app.route("/add_favorito/<int:producto_id>", methods=['POST'])
def add_favorito(producto_id):
    user_id = session.get('user_id')
    conn = get_db_connection()
    conn.execute('INSERT INTO favoritos (usuario_id, producto_id) VALUES (?, ?)', (user_id, producto_id))
    conn.commit()
    conn.close()
    flash('Producto añadido a favoritos', 'success')
    return redirect(url_for('menu'))

@app.route("/add_carrito/<int:producto_id>", methods=['POST'])
def add_carrito(producto_id):
    user_id = session.get('user_id')
    conn = get_db_connection()
    conn.execute('INSERT INTO carrito (usuario_id, producto_id) VALUES (?, ?)', (user_id, producto_id))
    conn.commit()
    conn.close()
    flash('Producto añadido al carrito', 'success')
    return redirect(url_for('menu'))

@app.route("/pedidos_cliente", methods=['GET'])
def pedidos_cliente():
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
    return render_template('general/PedidosCliente.html', pedidos=pedidos)

@app.route("/informacion", methods=['GET'])
def informacion():
    return render_template('general/informacion.html')

@app.route("/perfil_usuario", methods=['GET', 'POST'])
def perfil_usuario():
    user = {
        'name': session.get('user_name'),
        'email': session.get('user_email'),
        'image': session.get('user_image') or url_for('static', filename='img/defaultUser.png')
    }
    return render_template('Perfil/PerfilUsuario.html', user=user)

@app.route("/menu_restaurant")
def menu_restaurant():
    restaurant = {
        "name": session.get('user_name'),
        "address": "Dirección del Restaurante",
        "email": session.get('user_email'),
        "image": session.get('user_image')
    }
    return render_template('general/menu_empresas.html', restaurant=restaurant)

@app.route("/editar_perfil", methods=['GET', 'POST'])
def editar_perfil():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        current_password = request.form['current_password']
        new_password = request.form['new_password']

        conn = get_db_connection()
        user_id = session['user_id']
        user = conn.execute('SELECT * FROM usuarios WHERE id = ?', (user_id,)).fetchone()

        if user and check_password_hash(user['contrasena'], current_password):
            hashed_password = generate_password_hash(new_password) if new_password else user['contrasena']
            conn.execute('UPDATE usuarios SET nombre_usuario = ?, correo_electronico = ?, contrasena = ? WHERE id = ?', (name, email, hashed_password, user_id))
            conn.commit()
            flash('Perfil actualizado con éxito', 'success')
        else:
            flash('Contraseña actual incorrecta', 'error')

        conn.close()
        return redirect(url_for('perfil_usuario'))
    else:
        conn = get_db_connection()
        user_id = session['user_id']
        user = conn.execute('SELECT * FROM usuarios WHERE id = ?', (user_id,)).fetchone()
        conn.close()
        user = {'name': user['nombre_usuario'], 'email': user['correo_electronico'], 'password': user['contrasena']}
        return render_template('Perfil/EditarPerfil.html', user=user)

@app.route("/editar_perfil_empresa", methods=['GET', 'POST'])
def editar_perfil_empresa():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        current_password = request.form['current_password']
        new_password = request.form['new_password']

        conn = get_db_connection()
        company_id = session['user_id']
        company = conn.execute('SELECT * FROM usuarioEmpresa WHERE id = ?', (company_id,)).fetchone()

        if company and check_password_hash(company['contrasena'], current_password):
            hashed_password = generate_password_hash(new_password) if new_password else company['contrasena']
            conn.execute('UPDATE usuarioEmpresa SET nombre_usuario = ?, correo_electronico = ?, contrasena = ? WHERE id = ?', (name, email, hashed_password, company_id))
            conn.commit()
            flash('Perfil de empresa actualizado con éxito', 'success')
        else:
            flash('Contraseña actual incorrecta', 'error')

        conn.close()
        return redirect(url_for('perfil_empresa'))
    else:
        company = conn.execute('SELECT * FROM usuarioEmpresa WHERE id = ?', (session['user_id'],)).fetchone()
        return render_template('Perfil/EditarPerfilEmpresa.html', company=company)

@app.route("/soporte")
def soporte():
    return render_template('Perfil/Soporte.html')

@app.route("/perfil_empresa")
def perfil_empresa():
    company = {'name': session.get('user_name'), 'email': session.get('user_email'), 'image': session.get('user_image') or url_for('static', filename='img/defaultUser.png')}
    return render_template('Perfil/PerfilEmpresa.html', company=company)

@app.route("/direcciones_empresa")
def direcciones_empresa():
    addresses = [
        {'name': 'Oficina Central', 'address': '789 Calle Empresarial'},
        {'name': 'Sucursal', 'address': '101 Avenida Comercial'}
    ]
    return render_template('Perfil/DireccionesEmpresa.html', addresses=addresses)

@app.route("/membresia_empresa")
def membresia_empresa():
    return render_template('Perfil/MembresiaEmpresa.html')

@app.route("/soporte_empresa")
def soporte_empresa():
    return render_template('Perfil/SoporteEmpresa.html')

@app.route("/favoritos")
def favoritos():
    user_id = session.get('user_id')
    conn = get_db_connection()
    productos_favoritos = conn.execute('''
        SELECT Productos.* FROM Productos
        INNER JOIN favoritos ON Productos.id = favoritos.producto_id
        WHERE favoritos.usuario_id = ?
    ''', (user_id,)).fetchall()
    conn.close()
    return render_template('Favoritos.html', productos=productos_favoritos)

@app.route("/add_favorito/<int:producto_id>", methods=['POST'])
def add_favorito(producto_id):
    user_id = session.get('user_id')
    conn = get_db_connection()
    conn.execute('INSERT INTO favoritos (usuario_id, producto_id) VALUES (?, ?)', (user_id, producto_id))
    conn.commit()
    conn.close()
    flash('Producto añadido a favoritos', 'success')
    return redirect(url_for('menu'))

@app.route("/remove_favorito/<int:producto_id>", methods=['POST'])
def remove_favorito(producto_id):
    user_id = session.get('user_id')
    conn = get_db_connection()
    conn.execute('DELETE FROM favoritos WHERE usuario_id = ? AND producto_id = ?', (user_id, producto_id))
    conn.commit()
    conn.close()
    flash('Producto eliminado de favoritos', 'success')
    return redirect(url_for('favoritos'))

@app.route("/add_carrito/<int:producto_id>", methods=['POST'])
def add_carrito(producto_id):
    user_id = session.get('user_id')
    conn = get_db_connection()
    conn.execute('INSERT INTO carrito (usuario_id, producto_id) VALUES (?, ?)', (user_id, producto_id))
    conn.commit()
    conn.close()
    flash('Producto añadido al carrito', 'success')
    return redirect(url_for('menu'))

@app.route("/producto/<int:producto_id>")
def producto(producto_id):
    conn = get_db_connection()
    producto = conn.execute('SELECT * FROM Productos WHERE id = ?', (producto_id,)).fetchone()
    conn.close()
    return render_template('Producto.html', producto=producto)

if __name__ == "__main__":
    app.run(debug=True)