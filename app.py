"""
StudyGenie AI — Main Flask Application Entry Point
"""
import os
from flask import Flask
from flask_cors import CORS
from dotenv import load_dotenv

load_dotenv()

from config import Config
from models.db import init_db
from routes.auth_routes import auth_bp
from routes.subject_routes import subject_bp
from routes.document_routes import document_bp
from routes.ai_routes import ai_bp
from routes.quiz_routes import quiz_bp
from routes.planner_routes import planner_bp
from routes.dashboard_routes import dashboard_bp
from routes.page_routes import page_bp


def create_app() -> Flask:
    app = Flask(__name__)
    app.config.from_object(Config)

    CORS(app, supports_credentials=True)

    # Initialise SQLite database (creates studygenie.db + all tables if not exists)
    init_db()

    # Ensure upload and vector-store directories exist
    os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)
    os.makedirs(app.config["VECTOR_STORE_PATH"], exist_ok=True)

    # Register blueprints
    app.register_blueprint(page_bp)
    app.register_blueprint(auth_bp, url_prefix="/api/auth")
    app.register_blueprint(subject_bp, url_prefix="/api/subjects")
    app.register_blueprint(document_bp, url_prefix="/api/documents")
    app.register_blueprint(ai_bp, url_prefix="/api/ai")
    app.register_blueprint(quiz_bp, url_prefix="/api/quizzes")
    app.register_blueprint(planner_bp, url_prefix="/api/planner")
    app.register_blueprint(dashboard_bp, url_prefix="/api/dashboard")

    # Health endpoint
    @app.route("/api/health")
    def health():
        from flask import jsonify
        import sqlite3
        db_status = "connected"
        try:
            conn = sqlite3.connect(Config.db_path())
            conn.execute("SELECT 1")
            conn.close()
        except Exception:
            db_status = "unavailable"
        return jsonify({
            "status": "ok",
            "message": "StudyGenie AI backend is running",
            "database": db_status,
        })

    # Global error handlers
    @app.errorhandler(400)
    def bad_request(e):
        from flask import jsonify
        return jsonify({"error": "Bad request", "message": str(e)}), 400

    @app.errorhandler(401)
    def unauthorized(e):
        from flask import jsonify
        return jsonify({"error": "Unauthorized", "message": "Authentication required"}), 401

    @app.errorhandler(403)
    def forbidden(e):
        from flask import jsonify
        return jsonify({"error": "Forbidden", "message": "Access denied"}), 403

    @app.errorhandler(404)
    def not_found(e):
        from flask import jsonify, request
        if request.path.startswith("/api/"):
            return jsonify({"error": "Not found"}), 404
        from flask import render_template
        return render_template("index.html"), 404

    @app.errorhandler(413)
    def file_too_large(e):
        from flask import jsonify
        return jsonify({"error": "File too large", "message": "Maximum file size is 50 MB"}), 413

    @app.errorhandler(500)
    def internal_error(e):
        from flask import jsonify
        app.logger.error(f"Internal error: {e}")
        return jsonify({"error": "Internal server error"}), 500

    return app


if __name__ == "__main__":
    app = create_app()
    port = Config.PORT
    print(f"StudyGenie AI running on http://127.0.0.1:{port}/")
    app.run(host="0.0.0.0", port=port, debug=Config.DEBUG)
