from flask import Blueprint, jsonify, request
from models import db, Project, Competitor, Keyword, Post, ScrapeJob, ScrapeLog, GeneratedIdea, TrendAnalysis

from utils.trends import top_keywords

projects_bp = Blueprint('projects', __name__)

@projects_bp.route('', methods=['GET'])
def get_projects():
    projects = Project.query.all()
    result = []
    for p in projects:
        d = p.to_dict()
        d['competitor_count'] = Competitor.query.filter_by(project_id=p.id).count()
        d['post_count'] = Post.query.filter_by(project_id=p.id).count()
        result.append(d)
    return jsonify({'success': True, 'data': result})

@projects_bp.route('', methods=['POST'])
def create_project():
    data = request.get_json(silent=True) or {}
    if not (data.get('name') or '').strip():
        return jsonify({'success': False, 'message': 'Project name is required'}), 400
    project = Project(
        name=data.get('name').strip(),
        own_profile_name=data.get('own_profile_name'),
        own_profile_url=data.get('own_profile_url'),
        description=data.get('description')
    )
    db.session.add(project)
    db.session.commit()
    return jsonify({'success': True, 'data': project.to_dict()})

@projects_bp.route('/<int:id>', methods=['GET'])
def get_project(id):
    project = Project.query.get_or_404(id)
    return jsonify({'success': True, 'data': project.to_dict()})

@projects_bp.route('/<int:id>', methods=['PUT'])
def update_project(id):
    project = Project.query.get_or_404(id)
    data = request.json
    project.name = data.get('name', project.name)
    project.own_profile_name = data.get('own_profile_name', project.own_profile_name)
    project.own_profile_url = data.get('own_profile_url', project.own_profile_url)
    project.description = data.get('description', project.description)
    db.session.commit()
    return jsonify({'success': True, 'data': project.to_dict()})

@projects_bp.route('/<int:id>', methods=['DELETE'])
def delete_project(id):
    project = Project.query.get_or_404(id)
    Competitor.query.filter_by(project_id=id).delete()
    Post.query.filter_by(project_id=id).delete()
    Keyword.query.filter_by(project_id=id).delete()
    job_ids = [j.id for j in ScrapeJob.query.filter_by(project_id=id).all()]
    if job_ids:
        ScrapeLog.query.filter(ScrapeLog.job_id.in_(job_ids)).delete(synchronize_session=False)
    ScrapeJob.query.filter_by(project_id=id).delete()
    GeneratedIdea.query.filter_by(project_id=id).delete()
    TrendAnalysis.query.filter_by(project_id=id).delete()
    db.session.delete(project)
    db.session.commit()
    return jsonify({'success': True})

@projects_bp.route('/<int:id>/stats', methods=['GET'])
def project_stats(id):
    competitor_count = Competitor.query.filter_by(project_id=id).count()
    total_posts = Post.query.filter_by(project_id=id).count()
    
    latest_job = ScrapeJob.query.filter_by(project_id=id).order_by(ScrapeJob.started_at.desc()).first()
    new_posts_last_scrape = 0
    duplicates_last_scrape = 0
    if latest_job:
        logs = ScrapeLog.query.filter_by(job_id=latest_job.id).all()
        new_posts_last_scrape = sum(log.new_posts for log in logs)
        duplicates_last_scrape = sum(log.duplicates_skipped for log in logs)
        
    failed_scrapes = ScrapeLog.query.join(ScrapeJob).filter(ScrapeJob.project_id==id, ScrapeLog.status=='failed').count()
    last_scrape_date = latest_job.started_at.isoformat() if latest_job and latest_job.started_at else None
    
    generated_count = GeneratedIdea.query.filter_by(project_id=id).count()
    
    trends = TrendAnalysis.query.filter_by(project_id=id).order_by(TrendAnalysis.occurrence_count.desc()).limit(5).all()
    top_topics = [{'topic': t.topic, 'count': t.occurrence_count} for t in trends]
    
    analysis_count = Post.query.filter_by(project_id=id, ai_analyzed=True).count()
    manual_interventions = ScrapeLog.query.join(ScrapeJob).filter(ScrapeJob.project_id==id, ScrapeLog.manual_intervention==True).count()

    return jsonify({
        'success': True,
        'data': {
            'competitor_count': competitor_count,
            'total_posts': total_posts,
            'new_posts_last_scrape': new_posts_last_scrape,
            'duplicates_last_scrape': duplicates_last_scrape,
            'failed_scrapes': failed_scrapes,
            'last_scrape_date': last_scrape_date,
            'generated_count': generated_count,
            'top_topics': top_topics,
            'top_keywords': top_keywords(id, 8),
            'manual_interventions': manual_interventions,
            'analysis_count': analysis_count
        }
    })
