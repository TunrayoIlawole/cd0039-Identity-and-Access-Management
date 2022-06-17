from crypt import methods
import os
from flask import Flask, request, jsonify, abort
from sqlalchemy import exc
import json
from flask_cors import CORS

from .database.models import db_drop_and_create_all, setup_db, Drink
from .auth.auth import AuthError, requires_auth

app = Flask(__name__)
setup_db(app)
CORS(app)

'''
@TODO uncomment the following line to initialize the datbase
!! NOTE THIS WILL DROP ALL RECORDS AND START YOUR DB FROM SCRATCH
!! NOTE THIS MUST BE UNCOMMENTED ON FIRST RUN
!! Running this funciton will add one
'''
# db_drop_and_create_all()

# ROUTES
@app.route('/drinks', methods=['GET'])
def fetch_drinks():
    try:
        # Get all drinks from the database
        all_drinks = Drink.query.order_by(Drink.id).all()

        # Get the short version of each drink object
        returned_drinks = [drink.short() for drink in all_drinks]

        return jsonify({
            'success': True,
            'drinks': returned_drinks
        }), 200

    except Exception as e:
        print(e)
        abort(404)

@app.route('/drinks-detail', methods=['GET'])
@requires_auth('get:drinks-detail')
def fetch_drink_details(jwt):
    try:
        all_drinks = Drink.query.order_by(Drink.id).all()

        # Get the long version of each drink object
        returned_drinks = [drink.long() for drink in all_drinks]

        return jsonify({
            'success': True,
            'drinks': returned_drinks
        }), 200

    except:
        abort(404)


@app.route('/drinks', methods=['POST'])
@requires_auth('post:drinks')
def post_new_drinks(jwt):
    # Get the json from the request body
    body = request.get_json()

    # If title and recipe are not present in the json
    if not 'title' in body and not 'recipe' in body:
        abort(422)

    title = body.get('title')
    recipe = body.get('recipe')

    try:
        # Create new drink from the title and recipe from the request body
        new_drink = Drink(title=title, recipe=json.dumps(recipe))

        # Add the newly-created drink to the database
        new_drink.insert()

        return jsonify({
            'success': True,
            'drinks': [new_drink.long()]
        }), 200

    except:
        abort(422)


@app.route('/drinks/<id>', methods=['PATCH'])
@requires_auth('patch:drinks')
def update_drink(jwt, id):
    # Get the drink with the specified id
    drink = Drink.query.get(id)

    if drink:
        try:
            body = request.get_json()

            title = body.get('title')
            recipe = body.get('recipe')

            if title:
                drink.title = title
            if recipe:
                drink.recipe = json.dumps(recipe)

            # Update the drink in the database
            drink.update()

            return jsonify({
                'success': True,
                'drinks': [drink.long()]
            }), 200

        except:
            abort(422)
    
    # If drink does not exist
    else:
        abort(404)


@app.route('/drinks/<id>', methods=['DELETE'])
@requires_auth('delete:drinks')
def delete_drink(jwt, id):
    drink = Drink.query.get(id)

    if drink:
        try:
            drink.delete()

            return jsonify({
                'success': True,
                'deleted_drink': id
            }), 200

        except:
            abort(422)

    else:
        abort(404)





# Error Handling

@app.errorhandler(422)
def unprocessable():
    return jsonify({
        "success": False,
        "error": 422,
        "message": "unprocessable"
    }), 422


@app.errorhandler(404)
def not_found():
    return jsonify({
        'success': False,
        'error': 404,
        'message': 'resource not found'
    }), 404

@app.errorhandler(AuthError)
def handle_auth_error(e):
    return jsonify({
        'success': False,
        'error': e.status_code,
        'message': e.error
    })