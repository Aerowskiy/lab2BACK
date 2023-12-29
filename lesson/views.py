from lesson import app, db
from flask import Flask, jsonify, request
from datetime import datetime
from lesson.schemas import UserSchema, CategorySchema, RecordSchema, IncomeAccountSchema
from lesson.models import User, Category, Record, IncomeAccount
from marshmallow.exceptions import ValidationError



with app.app_context():
    db.create_all()
    db.session.commit()



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
    with app.app_context():
        user = User.query.get(user_id)

        if not user:
            return jsonify({'ERROR': f'User {user_id} does not exist'}), 404

        income_account = IncomeAccount.query.filter_by(user_id=user_id).first()

        if request.method == "GET":
            user_data = {
                'id': user.id,
                'username': user.username,
                'income_balance': income_account.balance if income_account else 0.0
            }
            return jsonify(user_data), 200

        elif request.method == "DELETE":
            try:
                db.session.delete(user)
                if income_account:
                    db.session.delete(income_account)
                db.session.commit()
                return jsonify({'MESSAGE': f'User {user_id} deleted'}), 200
            except Exception as e:
                return jsonify({'ERROR': str(e)}), 500



@app.route('/user', methods=['POST'])
def create_user():
    data = request.get_json()

    user_schema = UserSchema()
    try:
        user_data = user_schema.load(data)
    except ValidationError as err:
        return jsonify({'ERROR': err.messages}), 400

    new_user = User(
        username=user_data["username"],
        income_account=IncomeAccount(**user_data.get("income_account", {}))
    )

    with app.app_context():
        db.session.add(new_user)
        db.session.commit()

        user_response = {
            'user_id': new_user.id,
            'income_balance': new_user.income_account.balance
        }

        return jsonify(user_response), 200


@app.route('/users', methods=['GET'])
def get_users():
    with app.app_context():
        users_data = {
            user.id: {"username": user.username} for user in User.query.all()
        }
        return jsonify(users_data)



@app.route('/category', methods=['POST', 'GET'])
def manage_category():
    if request.method == 'GET':
        with app.app_context():
            categories_data = {
                category.id: {"name": category.name} for category in Category.query.all()
            }
            return jsonify(categories_data)

    elif request.method == 'POST':
        data = request.get_json()
        cat_schema = CategorySchema()
        try:
            cat_data = cat_schema.load(data)
        except ValidationError as err:
            return jsonify({'ERROR': err.messages}), 400

        new_category = Category(name=cat_data["name"])
        with app.app_context():
            db.session.add(new_category)
            db.session.commit()

            category_response = {
                "id": new_category.id,
                "name": new_category.name
            }

            return jsonify(category_response), 200


@app.route('/category/<int:cat_id>', methods=['DELETE'])
def delete_category(cat_id):
    with app.app_context():
        category = Category.query.get(cat_id)

        if not category:
            return jsonify({'ERROR': f'Category {cat_id} not found'}), 404

        db.session.delete(category)
        db.session.commit()
        return jsonify({'MESSAGE': f'Category {cat_id} deleted'}), 200


@app.route('/records', methods=['GET'])
def get_all_records():
    with app.app_context():
        records_data = {
            "records": [
                {
                    "id": record.id,
                    "user_id": record.user_id,
                    "category_id": record.category_id,
                    "amount": record.amount,
                    "created_at": record.created_at
                } for record in Record.query.all()
            ]
        }
        return jsonify(records_data)


@app.route('/record/<int:record_id>', methods=['GET', 'DELETE'])
def manage_record(record_id):
    with app.app_context():
        record = Record.query.get(record_id)

        if not record:
            return jsonify({"ERROR": f"Record {record_id} not found"}), 404

        if request.method == "GET":
            record_data = {
                "id": record.id,
                "user_id": record.user_id,
                "cat_id": record.category_id,
                "amount": record.amount,
                "created_at": record.created_at
            }
            return jsonify(record_data), 200

        elif request.method == "DELETE":
            db.session.delete(record)
            db.session.commit()
            return jsonify({'MESSAGE': f'Record {record_id} deleted'}), 200


@app.route('/record', methods=['POST', 'GET'])
def manage_records():
    if request.method == 'GET':
        user_id = request.args.get('user_id')
        category_id = request.args.get('category_id')

        if not user_id and not category_id:
           return jsonify({'ERROR': 'Specify user_id or category_id'}), 400


        query = Record.query
        if user_id:
            query = query.filter_by(user_id=user_id)
        if category_id:
            query = query.filter_by(category_id=category_id)

        need_records = query.all()
        print(need_records)
        records_data = {
           record.id: {
               "user_id": record.user_id,
               "cat_id": record.category_id,
               "amount": record.amount,
               "created_at": record.created_at
           } for record in need_records
        }
        return jsonify(records_data)

    elif request.method == 'POST':
        data = request.get_json()

        record_schema = RecordSchema()
        try:
            record_data = record_schema.load(data)
        except ValidationError as err:
            return jsonify({'ERROR': err.messages}), 400

        user_id = record_data['user_id']
        user = User.query.get(user_id)

        if not user:
            return jsonify({'ERROR': 'User not found'}), 404

        if user.income_account.balance < record_data['amount']:
            return jsonify({'ERROR': 'Insufficient funds'}), 400

        user.income_account.balance -= record_data['amount']
        db.session.commit()

        new_record = Record(
            user_id=user_id,
            category_id=record_data['category_id'],
            amount=record_data['amount']
        )

        with app.app_context():
            db.session.add(new_record)
            db.session.commit()

            record_response = {
                "id": new_record.id,
                "user_id": new_record.user_id,
                "cat_id": new_record.category_id,
                "amount": new_record.amount
            }

            return jsonify(record_response), 200

