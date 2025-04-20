from .main import main_bp
from .auth import auth_bp
from .data import data_bp
from .analysis import analysis_bp
from .api import api_bp

__all__ = [
    'main_bp',
    'auth_bp',
    'data_bp',
    'analysis_bp',
    'api_bp',
]