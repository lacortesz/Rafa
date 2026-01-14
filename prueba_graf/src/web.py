from flask import Flask, render_template, request, jsonify
import utility.utility as utils

app = Flask(__name__)

def procesar_seleccion(valor):
    print(f"Celda seleccionada: {valor}")
    return f"Recibido: {valor}"

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/seleccionar", methods=["POST"])
def seleccionar():
    data = request.json
    valor = data.get("valor")
    resultado = procesar_seleccion(valor)
    utils.graficar(valor)
    
    return jsonify({"resultado": resultado})

if __name__ == "__main__":
    app.run(debug=True)
