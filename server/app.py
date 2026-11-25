
#!/usr/bin/env python3

from flask import Flask, request, session, make_response
from flask_migrate import Migrate
from flask_restful import Api, Resource

from models import db, Article, User, ArticlesSchema, UserSchema


# Initialize Flask
app = Flask(__name__)

# Development-only secret key
app.secret_key = b'Y\xf1Xz\x00\xad|eQ\x80t \xca\x1a\x10K'

# Database configuration
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///app.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.json.compact = False

# Initialize database and API
db.init_app(app)
migrate = Migrate(app, db)
api = Api(app)


# Clear session
class ClearSession(Resource):

    def get(self):
        session.clear()
        return {}, 200

    def delete(self):
        session.clear()
        return make_response('', 204)


# List articles
class IndexArticle(Resource):

    def get(self):
        articles = [
            ArticlesSchema().dump(article)
            for article in Article.query.all()
        ]

        return articles, 200


# Show article with page-view limit
class ShowArticle(Resource):

    def get(self, id):

        session['page_views'] = (
            session.get('page_views', 0) + 1
        )

        if session['page_views'] > 3:
            return {
                'message': 'Maximum pageview limit reached'
            }, 401

        article = Article.query.filter_by(id=id).first()

        if not article:
            return {'error': 'Article not found'}, 404

        return ArticlesSchema().dump(article), 200


# LOGIN
class Login(Resource):

    def post(self):

        data = request.get_json(silent=True) or {}
        username = data.get('username')

        if not username:
            return {'message': 'Invalid login'}, 401

        user = User.query.filter_by(
            username=username
        ).first()

        if user:

            # Save the logged-in user's ID
            session['user_id'] = user.id

            # Return user information to React
            return UserSchema().dump(user), 200

        return {'message': 'Invalid login'}, 401


# LOGOUT
class Logout(Resource):

    def delete(self):

        # Remove user ID from the session
        session.pop('user_id', None)

        # 204: Success, no response body
        return make_response('', 204)


# CHECK SESSION
class CheckSession(Resource):

    def get(self):

        # Read current user's ID from session
        user_id = session.get('user_id')

        # No active session
        if not user_id:
            return {}, 401

        # Find logged-in user in database
        user = User.query.filter_by(
            id=user_id
        ).first()

        if not user:
            return {}, 401

        # Return logged-in user's information
        return UserSchema().dump(user), 200


# Register the routes
api.add_resource(ClearSession, '/clear')
api.add_resource(IndexArticle, '/articles')
api.add_resource(ShowArticle, '/articles/<int:id>')
api.add_resource(Login, '/login')
api.add_resource(Logout, '/logout')
api.add_resource(CheckSession, '/check_session')


if __name__ == '__main__':
    app.run(port=5555, debug=True)
