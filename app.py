import os
from flask import Flask
from config import Config
from extensions import db, login_manager, csrf, limiter


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    db.init_app(app)
    login_manager.init_app(app)
    csrf.init_app(app)
    limiter.init_app(app)

    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Please log in to access the admin panel.'
    login_manager.login_message_category = 'warning'

    from models.admin import Admin
    from models.payment import Payment
    from routes.kiosk import kiosk_bp
    from routes.auth import auth_bp
    from routes.admin import admin_bp

    app.register_blueprint(kiosk_bp)
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(admin_bp, url_prefix='/admin')

    @login_manager.user_loader
    def load_user(user_id):
        return Admin.query.get(int(user_id))

    @app.context_processor
    def inject_gym_name():
        return {'gym_name': app.config['GYM_NAME']}

    return app


if __name__ == '__main__':
    app = create_app()
    debug_mode = os.environ.get('FLASK_DEBUG', 'false').lower() == 'true'
    if debug_mode:
        app.run(debug=True, host='0.0.0.0', port=5000)
    else:
        from waitress import serve
        print('FitnessMadness running on http://localhost:5000')
        serve(app, host='0.0.0.0', port=5000, threads=4)
