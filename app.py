from flask import Flask, render_template, request, redirect, url_for, flash, session
import sqlite3

app = Flask(__name__)
app.secret_key = 'your_secret_key'

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
            imagen TEXT  -- Columna para almacenar imágenes
        )
    ''')
    # Crear tabla usuarioEmpresa
    conn.execute('''
        CREATE TABLE IF NOT EXISTS usuarioEmpresa (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre_usuario TEXT NOT NULL,
            correo_electronico TEXT NOT NULL UNIQUE,
            contrasena TEXT NOT NULL,
            imagen TEXT  -- Columna para almacenar imágenes
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
            tipoComida TEXT NOT NULL
        )
    ''')
    conn.commit()
    conn.close()

# Llama a la función para crear tablas
create_tables()

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
                return redirect(url_for('menu_restaurant'))
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

@app.route("/menu", methods=['GET', 'POST'])
def menu():
    user_name = session.get('user_name')
    user_image = session.get('user_image')
    return render_template('general/menu.html', user_name=user_name, user_image=user_image)

@app.route("/perfil_usuario", methods=['GET', 'POST'])
def perfil_usuario():
    user = {'name': session.get('user_name'), 'email': session.get('user_email'), 'image': session.get('user_image')}
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

@app.route("/direcciones")
def direcciones():
    return render_template('Perfil/Direcciones.html')

@app.route("/editar_perfil")
def editar_perfil():
    user = {'name': session.get('user_name'), 'email': session.get('user_email')}
    return render_template('Perfil/EditarPerfil.html', user=user)

@app.route("/metodos_pago")
def metodos_pago():
    return render_template('Perfil/MetodosPago.html')

@app.route("/membresia")
def membresia():
    return render_template('Perfil/Membresia.html')

@app.route("/soporte")
def soporte():
    return render_template('Perfil/Soporte.html')

if __name__ == "__main__":
    app.run(debug=True)
