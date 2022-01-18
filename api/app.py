from flask import Flask, jsonify, Blueprint
from flask_restful import Api
from flask_cors import CORS
import os

app = Flask(__name__, instance_relative_config=True, static_url_path='', static_folder='static/')

app.url_map.strict_slashes = False

CORS(app, resources={r'/v1/*'})
# db = MongoEngine(app)


# import your resources here.
from .resources.record import Record

api_blueprint = Blueprint('api', __name__)
api = Api(api_blueprint)

# define your endpoints here.
api.add_resource(Record, "/record", endpoint='record')
app.register_blueprint(api_blueprint, url_prefix='/v1')


@app.route('/')
def home():
    return jsonify({
        "message": "Welcome to DS Scrapper API!"
    })


@app.route('/v1')
def v1_home():
    return jsonify({
        "message": "Welcome to DS Scrapper v1 API!"
    })


@app.errorhandler(404)
def route_not_found(error):
    return jsonify({
        "message": "Route not found."
    }),


if __name__ == "__main__":
    print(True)
    port = int(os.environ.get('PORT'))
    app.run(port=port, host='127.0.0.1', debug=True)
