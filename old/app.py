from flask import Flask, render_template, request

app = Flask(__name__)

@app.route("/", methods=["GET", "POST"])
def index():
    saludo = None
    if request.method == "POST":
        nombre = request.form.get("nombre")
        saludo = f"Hola, {nombre} 👋" if nombre else "No ingresaste un nombre."
    return render_template("index.html", saludo=saludo)

if __name__ == "__main__":
    app.run(debug=True)
