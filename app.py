import os
import mimetypes
from flask import Flask, send_from_directory, jsonify
from flask_cors import CORS
from models import db
from config import Config
from database import seed_data

mimetypes.add_type('text/css', '.css')
mimetypes.add_type('application/javascript', '.js')

def create_app():
    app = Flask(__name__, static_folder='static')
    app.config.from_object(Config)
    CORS(app)
    db.init_app(app)


    # Register blueprints
    from routes.projects import projects_bp
    from routes.competitors import competitors_bp
    from routes.keywords import keywords_bp
    from routes.scraping import scraping_bp
    from routes.posts import posts_bp
    from routes.analysis import analysis_bp
    from routes.trends import trends_bp
    from routes.generator import generator_bp

    app.register_blueprint(projects_bp, url_prefix='/api/projects')
    app.register_blueprint(competitors_bp, url_prefix='/api/competitors')
    app.register_blueprint(keywords_bp, url_prefix='/api/keywords')
    app.register_blueprint(scraping_bp, url_prefix='/api/scraping')
    app.register_blueprint(posts_bp, url_prefix='/api/posts')
    app.register_blueprint(analysis_bp, url_prefix='/api/analysis')
    app.register_blueprint(trends_bp, url_prefix='/api/trends')
    app.register_blueprint(generator_bp, url_prefix='/api/generator')

    # Create media folder if not exists
    try:
        os.makedirs(os.path.join(app.root_path, app.config['MEDIA_FOLDER']), exist_ok=True)
    except OSError:
        pass  # read-only filesystem (e.g. Vercel): demo images ship with the deployment

    with app.app_context():
        db.create_all()
        seed_data(app)
        # Jobs left "running" by a previous process can never finish; mark them so the UI is truthful.
        from models import ScrapeJob
        from datetime import datetime
        for job in ScrapeJob.query.filter(ScrapeJob.status.in_(['running', 'awaiting_verification'])).all():
            job.status, job.ended_at = 'failed', datetime.utcnow()
        db.session.commit()

    @app.route('/')
    def index():
        return send_from_directory(app.static_folder, 'index.html')

    @app.route('/<path:path>')
    def serve_static(path):
        if path.startswith('api/'):
            return jsonify({'success': False, 'message': 'Not found'}), 404
        if os.path.exists(os.path.join(app.static_folder, path)):
            return send_from_directory(app.static_folder, path)
        return send_from_directory(app.static_folder, 'index.html')

    @app.errorhandler(404)
    def not_found(e):
        return jsonify({'success': False, 'message': 'Not found'}), 404

    @app.errorhandler(500)
    def internal_error(e):
        return jsonify({'success': False, 'message': 'Internal server error'}), 500

    return app

app = create_app()

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=int(os.environ.get('PORT', 5000)), debug=True, use_reloader=False)
