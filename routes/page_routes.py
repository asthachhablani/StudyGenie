"""
Page routes — serve HTML templates for the SPA-style frontend.
"""
from flask import Blueprint, render_template, session, redirect, url_for

page_bp = Blueprint("pages", __name__)


@page_bp.route("/")
def index():
    return render_template("index.html")


@page_bp.route("/login")
def login_page():
    if session.get("user_id"):
        return redirect("/dashboard")
    return render_template("login.html")


@page_bp.route("/register")
def register_page():
    if session.get("user_id"):
        return redirect("/dashboard")
    return render_template("register.html")


@page_bp.route("/dashboard")
def dashboard():
    return render_template("dashboard.html")


@page_bp.route("/subjects")
def subjects():
    return render_template("subjects.html")


@page_bp.route("/subjects/<subject_id>")
def subject(subject_id):
    return render_template("subject.html", subject_id=subject_id)


@page_bp.route("/upload")
def upload():
    return render_template("upload.html")


@page_bp.route("/study-assistant")
def study_assistant():
    return render_template("study_assistant.html")


@page_bp.route("/summary")
def summary():
    return render_template("summary.html")


@page_bp.route("/flashcards")
def flashcards():
    return render_template("flashcards.html")


@page_bp.route("/quiz")
def quiz():
    return render_template("quiz.html")


@page_bp.route("/study-plan")
def study_plan():
    return render_template("study_plan.html")


@page_bp.route("/revision")
def revision():
    return render_template("revision.html")


@page_bp.route("/profile")
def profile():
    return render_template("profile.html")
