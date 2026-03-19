from flask import Flask
from flask_cors import CORS
from .extensions import db
from .routes.transactions import transactions_bp
from .routes.categories import categories_bp
from .routes.budgets import budgets_bp
from .routes.analytics import analytics_bp

def create_app():
    app = Flask(__name__)
    import os
    basedir = os.path.abspath(os.path.dirname(__file__))
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'finance_tracker.db')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    CORS(app)
    db.init_app(app)

    # Register Blueprints
    app.register_blueprint(transactions_bp, url_prefix='/api/transactions')
    app.register_blueprint(categories_bp, url_prefix='/api/categories')
    app.register_blueprint(budgets_bp, url_prefix='/api/budgets')
    app.register_blueprint(analytics_bp, url_prefix='/api/analytics')
    
    from .routes.export import export_bp
    app.register_blueprint(export_bp, url_prefix='/api/export')

    with app.app_context():
        db.create_all()

    @app.route('/')
    def index():
        return app.send_static_file('index.html')

    @app.route('/<path:path>')
    def static_files(path):
        return app.send_static_file(path)

    return app

if __name__ == '__main__':
    app = create_app()
    # Ensure backend points to frontend dir
    import os
    app.static_folder = '../frontend'
    app.run(debug=True, port=5000)
