from app import app
from waitress import serve

print("Servidor iniciado con waitress en http://127.0.0.1:5005")
serve(app, host='127.0.0.1', port=5005)