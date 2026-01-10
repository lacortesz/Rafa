from flask import Flask, request, jsonify
import json

app = Flask(__name__)

@app.route('/webhook', methods=['POST'])
def receive_json():
    """
    Endpoint que recibe JSON por POST en puerto 5001.
    Uso: curl -X POST http://127.0.0.1:5001/webhook -H "Content-Type: application/json" -d '{"key":"value"}'
    """
    try:
        data = request.get_json()
        if data is None:
            return jsonify({"error": "No JSON data received"}), 400
        
        print("JSON recibido:")
        print(json.dumps(data, indent=2))
        
        # Procesar datos aquí según necesites
        # Ejemplo: guardar a archivo, procesar, enviar a otra función, etc.
        
        return jsonify({"status": "success", "received": data}), 200
    
    except Exception as e:
        print(f"Error: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({"status": "running"}), 200

if __name__ == "__main__":
    print("Iniciando servidor en http://127.0.0.1:5001")
    print("POST /webhook - Recibir JSON")
    print("GET /health - Health check")
    app.run(host="127.0.0.1", port=5001, debug=False)