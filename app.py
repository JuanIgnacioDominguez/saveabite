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
    conn.execute('''
        CREATE TABLE IF NOT EXISTS usuarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre_usuario TEXT NOT NULL,
            correo_electronico TEXT NOT NULL UNIQUE,
            contrasena TEXT NOT NULL
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
        conn.close()
        if user:
            session['user_id'] = user['id']
            session['user_name'] = user['nombre_usuario']
            return redirect(url_for('menu'))
        else:
            flash('Cuenta no encontrada o contraseña incorrecta', 'error')
            return redirect(url_for('login'))
    return render_template('general/Iniciarsesion.html')

@app.route("/register", methods=['GET', 'POST'])
def register():
    if request.method == 'POST']:
        name = request.form['name']
        email = request.form['email']
        password = request.form['password']

        if not name or not email or not password:
            flash('Por favor, complete todas las casillas', 'error')
            return redirect(url_for('register'))

        conn = get_db_connection()
        try:
            conn.execute('INSERT INTO usuarios (nombre_usuario, correo_electronico, contrasena) VALUES (?, ?, ?)', (name, email, password))
            conn.commit()
        except sqlite3.IntegrityError:
            flash('El correo electrónico ya está registrado', 'error')
            return redirect(url_for('register'))
        finally:
            conn.close()
        return redirect(url_for('menu'))
    return render_template('general/Registrarse.html')

@app.route("/menu", methods=['GET', 'POST'])
def menu():
    user_name = session.get('user_name')
    return render_template('general/menu.html', user_name=user_name)

@app.route("/perfil_usuario", methods=['GET', 'POST'])
def perfil_usuario():
    user = {'name': session.get('user_name'), 'email': 'user@example.com', 'password': '********'}
    return render_template('Perfil/PerfilUsuario.html', user=user)

@app.route("/direcciones", methods=['GET', 'POST'])
def direcciones():
    addresses = [
        {'name': 'Casa', 'address': 'Calle Falsa 123', 'primary': True},
        {'name': 'Trabajo', 'address': 'Av. Siempreviva 742', 'primary': False}
    ]
    return render_template('Perfil/Direcciones.html', addresses=addresses)

@app.route("/editar_perfil", methods=['GET', 'POST'])
def editar_perfil():
    user = {'name': session.get('user_name'), 'email': 'user@example.com', 'password': '********'}
    return render_template('Perfil/EditarPerfil.html', user=user)

@app.route("/metodos_pago", methods=['GET', 'POST'])
def metodos_pago():
    payment_methods = [
        {'brand': 'Visa', 'number': '**** **** **** 1234', 'primary': True},
        {'brand': 'MasterCard', 'number': '**** **** **** 5678', 'primary': False}
    ]
    return render_template('Perfil/MetodosPago.html', payment_methods=payment_methods)

@app.route("/soporte", methods=['GET', 'POST'])
def soporte():
    if request.method == 'POST':
        # Lógica para manejar el envío de mensajes de soporte
        return redirect(url_for('soporte_exitoso'))
    return render_template('Perfil/Soporte.html')

@app.route("/soporte_exitoso", methods=['GET'])
def soporte_exitoso():
    return render_template('Perfil/SoporteExitoso.html')

@app.route("/informacion", methods=['GET'])
def informacion():
    return render_template('general/Informacion.html')

if __name__ == "__main__":
    app.run(debug=True)