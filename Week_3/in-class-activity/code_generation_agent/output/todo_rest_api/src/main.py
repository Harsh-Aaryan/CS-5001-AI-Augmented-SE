from flask import Flask, request, jsonify
from typing import List, Dict, Optional, Union

app = Flask(__name__)

# In-memory storage for todos
todos: List[Dict[str, Union[int, str]]] = []
next_id = 1

@app.route('/todos', methods=['GET'])
def get_todos():
    """List all todos"""
    return jsonify(todos)

@app.route('/todos', methods=['POST'])
def create_todo():
    """Create a new todo"""
    global next_id
    data = request.get_json()
    if not data or 'title' not in data or not isinstance(data['title'], str) or not data['title'].strip():
        return jsonify({'error': 'Title is required and must be a non-empty string'}), 400

    todo = {
        'id': next_id,
        'title': data['title'].strip(),
        'status': 'pending'
    }
    todos.append(todo)
    next_id += 1
    return jsonify(todo), 201

@app.route('/todos/<int:todo_id>', methods=['GET'])
def get_todo(todo_id: int):
    """Get a todo by ID"""
    todo = next((t for t in todos if t['id'] == todo_id), None)
    if todo is None:
        return jsonify({'error': 'Todo not found'}), 404
    return jsonify(todo)

@app.route('/todos/<int:todo_id>', methods=['PUT'])
def update_todo(todo_id: int):
    """Update a todo"""
    todo = next((t for t in todos if t['id'] == todo_id), None)
    if todo is None:
        return jsonify({'error': 'Todo not found'}), 404

    data = request.get_json()
    if not data:
        return jsonify({'error': 'No data provided'}), 400

    if 'title' in data:
        if not isinstance(data['title'], str) or not data['title'].strip():
            return jsonify({'error': 'Title must be a non-empty string'}), 400
        todo['title'] = data['title'].strip()

    if 'status' in data:
        if data['status'] not in ['pending', 'done']:
            return jsonify({'error': 'Status must be either "pending" or "done"'}), 400
        todo['status'] = data['status']

    return jsonify(todo)

@app.route('/todos/<int:todo_id>', methods=['DELETE'])
def delete_todo(todo_id: int):
    """Delete a todo"""
    global todos
    todo = next((t for t in todos if t['id'] == todo_id), None)
    if todo is None:
        return jsonify({'error': 'Todo not found'}), 404

    todos = [t for t in todos if t['id'] != todo_id]
    return '', 204

@app.errorhandler(400)
def bad_request(error):
    return jsonify({'error': 'Bad request'}), 400

@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Not found'}), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({'error': 'Internal server error'}), 500

if __name__ == '__main__':
    app.run(debug=True)
