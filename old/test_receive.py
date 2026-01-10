# Con Python
import requests
requests.post("http://127.0.0.1:5001/webhook", json={"symbol":"AAPL","price":150.5})