from flask import Blueprint, render_template

#define main_bp blueprint

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def home():
    return render_template('main/home.html')