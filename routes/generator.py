from flask import Blueprint, jsonify, request, current_app
from models import db, GeneratedIdea
from ai.analyzer import generate_ideas_for_project

generator_bp = Blueprint('generator_bp', __name__)

@generator_bp.route('/project/<int:project_id>/generate', methods=['POST'])
def generate_ideas(project_id):
    data = request.get_json(silent=True) or {}
    try:
        count = int(data.get('count', 10))
    except (TypeError, ValueError):
        return jsonify({'success': False, 'message': 'count must be a number'}), 400
    count = max(1, min(count, 50))

    app = current_app._get_current_object()
    result = generate_ideas_for_project(project_id, count, app)
    if result is None:
        return jsonify({'success': False, 'message': 'Project not found'}), 404

    return jsonify({
        'success': True,
        'data': {
            'ideas': result['ideas'],
            'count_generated': len(result['ideas']),
            'requested': result['requested'],
            'provider': result['provider'],
            'warnings': result['warnings']
        }
    })

@generator_bp.route('/project/<int:project_id>/ideas', methods=['GET'])
def get_ideas(project_id):
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    is_used = request.args.get('is_used')
    
    query = GeneratedIdea.query.filter_by(project_id=project_id)
    if is_used is not None:
        is_used_bool = is_used.lower() == 'true'
        query = query.filter_by(is_used=is_used_bool)
        
    pagination = query.order_by(GeneratedIdea.generated_at.desc()).paginate(page=page, per_page=per_page, error_out=False)
    
    return jsonify({
        'success': True,
        'data': {
            'ideas': [i.to_dict() for i in pagination.items],
            'total': pagination.total,
            'pages': pagination.pages,
            'current_page': pagination.page,
            'per_page': pagination.per_page
        }
    })

@generator_bp.route('/idea/<int:id>', methods=['PUT'])
def update_idea(id):
    idea = GeneratedIdea.query.get_or_404(id)
    data = request.json
    
    if 'is_used' in data:
        idea.is_used = data['is_used']
    if 'topic' in data:
        idea.topic = data['topic']
    if 'update_copy' in data:
        idea.update_copy = data['update_copy']
    if 'call_to_action' in data:
        idea.call_to_action = data['call_to_action']
        
    db.session.commit()
    return jsonify({'success': True, 'data': idea.to_dict()})

@generator_bp.route('/idea/<int:id>', methods=['DELETE'])
def delete_idea(id):
    idea = GeneratedIdea.query.get_or_404(id)
    db.session.delete(idea)
    db.session.commit()
    return jsonify({'success': True})

@generator_bp.route('/project/<int:project_id>/ideas/stats', methods=['GET'])
def get_idea_stats(project_id):
    total = GeneratedIdea.query.filter_by(project_id=project_id).count()
    used = GeneratedIdea.query.filter_by(project_id=project_id, is_used=True).count()
    unused = total - used
    
    gemini = GeneratedIdea.query.filter_by(project_id=project_id, ai_provider='gemini').count()
    grok = GeneratedIdea.query.filter_by(project_id=project_id, ai_provider='grok').count()
    
    return jsonify({
        'success': True,
        'data': {
            'total': total,
            'used': used,
            'unused': unused,
            'by_provider': {
                'gemini': gemini,
                'grok': grok
            }
        }
    })
