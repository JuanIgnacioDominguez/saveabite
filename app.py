from flask import Flask, render_template
from pymongo import MongoClient

app = Flask(__name__)

# ENTRADA DE MONGO AL PROYECTO
client = MongoClient('localhost', 27017)
db = client.flask_db
todos = db.todos

# RUTA PARA LA PÁGINA PRINCIPAL
@app.route("/", methods=['GET', 'POST'])
def index():
    return render_template('index.html')

@app.route('/Perfil')
def perfil():
    user = {
        "name": "Juan Perez",
        "email": "juan.perez@example.com"
    }
    return render_template('profile.html', user=user)

@app.route('/Direcciones')
def direcciones():
    addresses = [
        {"name": "Casa", "address": "123 Calle Falsa, Ciudad", "primary": True},
        {"name": "Trabajo", "address": "456 Avenida Siempre Viva, Ciudad", "primary": False},
        {"name": "Otro", "address": "789 Calle Ejemplo, Ciudad", "primary": False},
    ]
    return render_template('addresses.html', addresses=addresses)

@app.route('/EditarPerfil')
def editar_perfil():
    user = {
        "name": "Juan Perez",
        "email": "juan.perez@example.com",
        "password": "********"
    }
    return render_template('edit_profile.html', user=user)

@app.route('/MetodosPago')
def metodos_de_pago():
    payment_methods = [
        {"brand": "Visa", "number": "**** **** **** 1234", "primary": True},
        {"brand": "Mastercard", "number": "**** **** **** 5678", "primary": False},
        {"brand": "Amex", "number": "**** **** **** 9012", "primary": False},
    ]
    return render_template('payment_methods.html', payment_methods=payment_methods)

@app.route('/Soporte', methods=['GET', 'POST'])
def soporte():
    if request.method == 'POST':
        message = request.form['message']
        # Aquí podrías guardar el mensaje en una base de datos o enviarlo por correo electrónico
        return redirect(url_for('soporte_exito'))
    return render_template('support.html')

@app.route('/SoporteExito')
def soporte_exito():
    return render_template('support_success.html')

if __name__ == '__main__':
    app.run(debug=True)
