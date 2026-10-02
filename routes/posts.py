from datetime import datetime, timedelta
from flask import Blueprint, jsonify, request
from sqlalchemy import or_, and_
from models import db, Post, Competitor, ScrapeJob

posts_bp = Blueprint('posts_bp', __name__)


def _parse_day(value):
    try:
        return datetime.strptime(value, '%Y-%m-%d')
    except (TypeError, ValueError):
        return None


@posts_bp.route('/project/<int:project_id>', methods=['GET'])
def get_posts(project_id):
    q = request.args.get('q')
    competitor_id = request.args.get('competitor_id', type=int)
    date_from = _parse_day(request.args.get('date_from'))
    date_to = _parse_day(request.args.get('date_to'))
    topic = request.args.get('topic')
    keyword = request.args.get('keyword')
    page = request.args.get('page', 1, type=int)
    per_page = min(request.args.get('per_page', 20, type=int), 100)

    query = Post.query.filter_by(project_id=project_id)

    if q:
        like = f'%{q}%'
        query = query.filter(or_(Post.post_text.ilike(like), Post.ai_keywords.ilike(like),
                                 Post.detected_keywords.ilike(like), Post.competitor_name.ilike(like)))
    if keyword:
        like = f'%{keyword}%'
        query = query.filter(or_(Post.ai_keywords.ilike(like), Post.detected_keywords.ilike(like), Post.post_text.ilike(like)))
    if competitor_id:
        query = query.filter(Post.competitor_id == competitor_id)

    # Filter on the published date; fall back to the scrape date when the source gave none.
    if date_from:
        query = query.filter(or_(
            and_(Post.published_date.isnot(None), Post.published_date >= date_from.strftime('%Y-%m-%d')),
            and_(Post.published_date.is_(None), Post.scrape_date >= date_from)))
    if date_to:
        query = query.filter(or_(
            and_(Post.published_date.isnot(None), Post.published_date <= date_to.strftime('%Y-%m-%d')),
            and_(Post.published_date.is_(None), Post.scrape_date < date_to + timedelta(days=1))))
    if topic:
        query = query.filter(or_(Post.ai_main_topic == topic, Post.detected_topic == topic))

    pagination = query.order_by(Post.scrape_date.desc()).paginate(page=page, per_page=per_page, error_out=False)

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


@posts_bp.route('/<int:id>', methods=['GET'])
def get_post(id):
    post = Post.query.get_or_404(id)
    data = post.to_dict()
    data['local_image_paths'] = [img for img in data.get('images', []) if isinstance(img, str)]

    # Scraping history for this post: when/in which run it was first collected, and how often it was seen again.
    job = db.session.get(ScrapeJob, post.scrape_job_id) if post.scrape_job_id else None
    data['collected_in_job'] = job.to_dict() if job else None
    return jsonify({'success': True, 'data': data})


@posts_bp.route('/project/<int:project_id>/topics', methods=['GET'])
def get_topics(project_id):
    topics = set()
    for p in Post.query.filter_by(project_id=project_id).all():
        if p.ai_main_topic:
            topics.add(p.ai_main_topic)
        elif p.detected_topic:
            topics.add(p.detected_topic)
    return jsonify({'success': True, 'data': sorted(topics)})
