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

if __name__ == '__main__':
    app.run(debug=True)
