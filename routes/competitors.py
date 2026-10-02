from flask import Blueprint, jsonify, request
from models import db, Competitor, Post, ScrapeLog

competitors_bp = Blueprint('competitors', __name__)

@competitors_bp.route('/project/<int:project_id>', methods=['GET'])
def get_competitors(project_id):
    competitors = Competitor.query.filter_by(project_id=project_id).all()
    result = []
    for c in competitors:
        d = c.to_dict()
        d['post_count'] = Post.query.filter_by(competitor_id=c.id).count()
        result.append(d)
    return jsonify({'success': True, 'data': result})

@competitors_bp.route('/project/<int:project_id>', methods=['POST'])
def create_competitor(project_id):
    data = request.get_json(silent=True) or {}
    name = (data.get('name') or '').strip()
    url = (data.get('gmaps_url') or data.get('google_maps_url') or '').strip()
    if not name or not url.lower().startswith('http'):
        return jsonify({'success': False, 'message': 'A name and a Google Maps URL (starting with http) are required'}), 400
    if Competitor.query.filter_by(project_id=project_id, gmaps_url=url).first():
        return jsonify({'success': False, 'message': 'This competitor is already in the project'}), 409
    competitor = Competitor(
        project_id=project_id,
        name=name,
        gmaps_url=url,
        notes=data.get('notes')
    )
    db.session.add(competitor)
    db.session.commit()
    return jsonify({'success': True, 'data': competitor.to_dict()})

@competitors_bp.route('/<int:id>', methods=['GET'])
def get_competitor(id):
    competitor = Competitor.query.get_or_404(id)
    data = competitor.to_dict()
    data['post_count'] = Post.query.filter_by(competitor_id=id).count()
    return jsonify({'success': True, 'data': data})

@competitors_bp.route('/<int:id>', methods=['PUT'])
def update_competitor(id):
    competitor = Competitor.query.get_or_404(id)
    data = request.get_json(silent=True) or {}
    new_url = (data.get('gmaps_url') or data.get('google_maps_url') or competitor.gmaps_url).strip()
    if not new_url.lower().startswith('http'):
        return jsonify({'success': False, 'message': 'Google Maps URL must start with http'}), 400
    competitor.name = (data.get('name') or competitor.name).strip()
    competitor.gmaps_url = new_url
    competitor.notes = data.get('notes', competitor.notes)
    db.session.commit()
    return jsonify({'success': True, 'data': competitor.to_dict()})

@competitors_bp.route('/<int:id>', methods=['DELETE'])
def delete_competitor(id):
    competitor = Competitor.query.get_or_404(id)
    Post.query.filter_by(competitor_id=id).delete()
    logs = ScrapeLog.query.filter_by(competitor_id=id).all()
    for log in logs:
        log.competitor_id = None
    db.session.delete(competitor)
    db.session.commit()
    return jsonify({'success': True})

@competitors_bp.route('/<int:id>/posts', methods=['GET'])
def get_competitor_posts(id):
    posts = Post.query.filter_by(competitor_id=id).all()
    return jsonify({'success': True, 'data': [p.to_dict() for p in posts]})
