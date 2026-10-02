import threading
from flask import Blueprint, jsonify, request, current_app
from models import db, Post
from config import ON_VERCEL
from ai.analyzer import analyze_project, analyze_post as analyze_single_post

analysis_bp = Blueprint('analysis_bp', __name__)

@analysis_bp.route('/project/<int:project_id>/run', methods=['POST'])
def run_analysis(project_id):
    app = current_app._get_current_object()
    if ON_VERCEL:
        # Serverless functions are frozen once the response is sent, so background threads would never finish.
        analyze_project(project_id, app)
        return jsonify({'success': True, 'data': {'task_id': project_id, 'message': 'Analysis complete'}})
    t = threading.Thread(target=analyze_project, args=(project_id, app), daemon=True)
    t.start()
    return jsonify({'success': True, 'data': {'task_id': project_id, 'message': 'Analysis started'}})

@analysis_bp.route('/project/<int:project_id>/status', methods=['GET'])
def get_analysis_status(project_id):
    total_posts = Post.query.filter_by(project_id=project_id).count()
    analyzed_posts = Post.query.filter_by(project_id=project_id, ai_analyzed=True).count()
    pending_posts = total_posts - analyzed_posts
    percentage = (analyzed_posts / total_posts * 100) if total_posts > 0 else 0
    
    return jsonify({
        'success': True,
        'data': {
            'total_posts': total_posts,
            'analyzed_posts': analyzed_posts,
            'pending_posts': pending_posts,
            'percentage': round(percentage, 2)
        }
    })

@analysis_bp.route('/project/<int:project_id>/results', methods=['GET'])
def get_analysis_results(project_id):
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    
    pagination = Post.query.filter_by(project_id=project_id, ai_analyzed=True).paginate(page=page, per_page=per_page, error_out=False)
    
    return jsonify({
        'success': True,
        'data': {
            'posts': [p.to_dict() for p in pagination.items],
            'total': pagination.total,
            'pages': pagination.pages,
            'current_page': pagination.page,
            'per_page': pagination.per_page
        }
    })

@analysis_bp.route('/analyze-post/<int:post_id>', methods=['POST'])
def analyze_post_route(post_id):
    app = current_app._get_current_object()
    result = analyze_single_post(post_id, app)
    if result:
        return jsonify({'success': True, 'data': result})
    return jsonify({'success': False, 'message': 'Analysis failed'}), 500
