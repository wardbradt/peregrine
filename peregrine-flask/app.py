from flask import Flask
app = Flask(__name__)

@app.route('/')
def landing():
    return 'Hello, Landing Page!'
