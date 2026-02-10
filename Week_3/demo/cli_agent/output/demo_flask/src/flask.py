import os
from flask import Flask, request, jsonify

app = Flask(__name__)

@app.route('/')
def home():
    """Root endpoint that returns a welcome message."""
    return "Welcome to the minimal Flask project!"

@app.route('/echo', methods=['GET', 'POST'])
def echo():
    """Echo endpoint that returns the request data."""
    if request.method == 'GET':
        return jsonify({"method": "GET", "data": request.args.to_dict()})
    elif request.method == 'POST':
        return jsonify({"method": "POST", "data": request.json or request.form.to_dict()})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
