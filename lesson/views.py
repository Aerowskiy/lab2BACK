from lesson import app
from flask import Flask, jsonify, request
from datetime import datetime
import uuid


users = {}
categories = {}
records = {}



@app.route("/")
def all_works():
    return f"<p>all works!</p><a href='/healthcheck'>Health Status</a>"


@app.route("/healthcheck")
def healthcheck():
    resp = jsonify(date=datetime.now(), status="OK")
    resp.status_code = 200
    return resp



@app.route("/user/<int:user_id>", methods=['GET', 'DELETE'])
def control_users():
    if request.method == 'GET':
        user_data = users.get(user_id)
        if not user_data:
            return jsonify({"error": "User not found"}), 404
        return jsonify(user_data)
    elif request.method == 'DELETE':
        user_data = users.pop(user_id, None)
        if not user_data:
            return jsonify({"error": "User not found"}), 404
        return jsonify(user_data)



@app.route('/user', methods=['POST'])
def create_user():
    user_data = request.get_json()
    if "username" not in user_data:
        return jsonify({"error": "username are required"}), 400
    user_id = uuid.uuid4().hex
    user = {"id": user_id, **user_data}
    users[user_id] = user
    return jsonify(user)


@app.route('/users', methods=['GET'])
def get_users():
    return jsonify(list(users.values()))


@app.route('/category', methods=['POST', 'GET', 'DELETE'])
def manage_category():
    if request.method == 'POST':
        category_data = request.get_json()
        if "name" not in category_data:
            return jsonify({"error": "name are required"}), 400
        category_id = uuid.uuid4().hex
        category = {"id": category_id, **category_data}
        categories[category_id] = category
        return jsonify(category)

    elif request.method == 'GET':
        return jsonify(list(categories.values()))

    elif request.method == 'DELETE':
        category_id = request.args.get('id')
        if category_id:
            category = categories.pop(category_id, None)
            if not category:
                return jsonify({"error": f"Category id {category_id} not found"}), 404
            return jsonify(category)
        else:
            categories.clear()
            return jsonify({"message": "Categories are deleted"})


@app.route('/record/<int:record_id>', methods=['GET', 'DELETE'])
def check_record():
    if request.method == 'GET':
        record = records.get(record_id)
        if not record:
            return jsonify({"error": "Record not found"}), 404
        return jsonify(record)

    elif request.method == 'DELETE':
        record = records.pop(record_id, None)
        if not record:
            return jsonify({"error": "Record not found"}), 404
        return jsonify(record)


@app.route('/record', methods=['POST', 'GET'])
def create_record():
    if request.method == 'POST':
        record_data = request.get_json()
        user_id = record_data.get('user_id')
        category_id = record_data.get('category_id')

        if not user_id or not category_id:
            return jsonify({"error": "Both user_id and category_id are required"}), 400
        if user_id not in users:
            return jsonify({"error": f"User with id {user_id} not found"}), 404
        if category_id not in categories:
            return jsonify({"error": f"Category with id {category_id} not found"}), 404

        record_id = uuid.uuid4().hex
        record = {"id": record_id, **record_data}
        records[record_id] = record
        return jsonify(record)
    elif request.method == 'GET':
        user_id = request.args.get('user_id')
        category_id = request.args.get('category_id')
        if not user_id and not category_id:
            return jsonify({"error": "Specify user_id or category_id"}), 400
        filtered_records = [
            r for r in records.values() if (not user_id or r['user_id'] == user_id) or (not category_id or r['category_id'] == category_id)
        ]
        return jsonify(filtered_records)
