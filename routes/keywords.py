from flask import Blueprint, jsonify, request
from models import db, Keyword

keywords_bp = Blueprint('keywords', __name__)

@keywords_bp.route('/project/<int:project_id>', methods=['GET'])
def get_keywords(project_id):
    keywords = Keyword.query.filter_by(project_id=project_id).all()
    return jsonify({'success': True, 'data': [k.to_dict() for k in keywords]})

@keywords_bp.route('/project/<int:project_id>', methods=['POST'])
def add_keyword(project_id):
    data = request.get_json(silent=True) or {}
    text = (data.get('keyword') or '').strip()
    if not text:
        return jsonify({'success': False, 'message': 'Keyword is required'}), 400
    existing = Keyword.query.filter(Keyword.project_id == project_id, db.func.lower(Keyword.keyword) == text.lower()).first()
    if existing:
        return jsonify({'success': False, 'message': 'Keyword already exists'}), 409
    keyword = Keyword(
        project_id=project_id,
        keyword=text
    )
    db.session.add(keyword)
    db.session.commit()
    return jsonify({'success': True, 'data': keyword.to_dict()})

@keywords_bp.route('/<int:id>', methods=['DELETE'])
def delete_keyword(id):
    keyword = Keyword.query.get_or_404(id)
    db.session.delete(keyword)
    db.session.commit()
    return jsonify({'success': True})
