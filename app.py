from flask import Flask, render_template, request, redirect, url_for, flash
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
            return redirect(url_for('menu'))
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
    return render_template('general/menu.html')

if __name__ == "__main__":
    app.run(debug=True)