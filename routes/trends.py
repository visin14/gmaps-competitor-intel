from flask import Blueprint, jsonify
from models import TrendAnalysis
from utils.trends import calculate_trends as compute_trends, competitor_patterns, top_keywords

trends_bp = Blueprint('trends_bp', __name__)


@trends_bp.route('/project/<int:project_id>/calculate', methods=['POST'])
def calculate_trends(project_id):
    trends = compute_trends(project_id)
    return jsonify({'success': True, 'data': [t.to_dict() for t in trends]})


@trends_bp.route('/project/<int:project_id>', methods=['GET'])
def get_trends(project_id):
    trends = TrendAnalysis.query.filter_by(project_id=project_id).order_by(TrendAnalysis.occurrence_count.desc()).all()
    return jsonify({'success': True, 'data': [t.to_dict() for t in trends]})


@trends_bp.route('/project/<int:project_id>/keywords', methods=['GET'])
def get_keywords(project_id):
    return jsonify({'success': True, 'data': top_keywords(project_id)})


@trends_bp.route('/project/<int:project_id>/patterns', methods=['GET'])
def get_patterns(project_id):
    return jsonify({'success': True, 'data': competitor_patterns(project_id)})
