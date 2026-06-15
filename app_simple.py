from flask import Flask

app = Flask(__name__)

@app.route('/')
def home():
    return "<h1>Flask funciona</h1>"

if __name__ == '__main__':
    # Forzar servidor en un solo hilo, sin reloader, puerto fijo
    app.run(host='127.0.0.1', port=5005, debug=False, use_reloader=False, threaded=False)