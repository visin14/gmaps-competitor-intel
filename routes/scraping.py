import threading
from datetime import datetime
from flask import Blueprint, jsonify, request, current_app
from models import db, ScrapeJob, ScrapeLog, Competitor
from config import ON_VERCEL
from scraper.gmaps_scraper import run_scrape_job

scraping_bp = Blueprint('scraping_bp', __name__)

SCRAPE_EVENTS = {}


def run_scrape_thread(app, job_id, competitor_ids, pause_event):
    try:
        run_scrape_job(app, job_id, competitor_ids, pause_event)
    except Exception:
        with app.app_context():
            db.session.rollback()
            job = db.session.get(ScrapeJob, job_id)
            if job:
                job.status = 'failed'
                job.ended_at = datetime.utcnow()
                db.session.commit()
    finally:
        SCRAPE_EVENTS.pop(job_id, None)


@scraping_bp.route('/start', methods=['POST'])
def start_scrape():
    if ON_VERCEL:
        return jsonify({'success': False, 'message': 'Live scraping needs a local Chrome browser and is not available on this hosted demo. '
                                                     'Run the app locally to scrape; the stored repository here is fully browsable.'}), 503
    data = request.get_json(silent=True) or {}
    project_id = data.get('project_id')
    competitor_ids = data.get('competitor_ids') or []

    valid_ids = [c.id for c in Competitor.query.filter(Competitor.project_id == project_id,
                                                       Competitor.id.in_(competitor_ids)).all()] if competitor_ids else []
    if not valid_ids:
        return jsonify({'success': False, 'message': 'Select at least one competitor from this project'}), 400

    job = ScrapeJob(project_id=project_id, total_competitors=len(valid_ids))
    db.session.add(job)
    db.session.commit()

    event = threading.Event()
    SCRAPE_EVENTS[job.id] = event

    app = current_app._get_current_object()
    threading.Thread(target=run_scrape_thread, args=(app, job.id, valid_ids, event), daemon=True).start()

    return jsonify({'success': True, 'data': {'job_id': job.id}})


@scraping_bp.route('/job/<int:job_id>/status', methods=['GET'])
def get_job_status(job_id):
    job = ScrapeJob.query.get_or_404(job_id)
    logs = ScrapeLog.query.filter_by(job_id=job.id).all()

    data = job.to_dict()
    data['logs'] = [log.to_dict() for log in logs]
    return jsonify({'success': True, 'data': data})


@scraping_bp.route('/job/<int:job_id>/resume', methods=['POST'])
def resume_job(job_id):
    """Called after the user has completed the CAPTCHA/verification in the scraper's browser window."""
    ScrapeJob.query.get_or_404(job_id)
    event = SCRAPE_EVENTS.get(job_id)
    if event is None:
        return jsonify({'success': False, 'message': 'This job is no longer running'}), 409
    event.set()
    return jsonify({'success': True})


@scraping_bp.route('/project/<int:project_id>/jobs', methods=['GET'])
def get_project_jobs(project_id):
    jobs = ScrapeJob.query.filter_by(project_id=project_id).order_by(ScrapeJob.started_at.desc()).all()
    result = []
    for job in jobs:
        d = job.to_dict()
        logs = ScrapeLog.query.filter_by(job_id=job.id).all()
        d['summary'] = {
            'new_posts': sum(log.new_posts or 0 for log in logs),
            'duplicates_skipped': sum(log.duplicates_skipped or 0 for log in logs)
        }
        result.append(d)
    return jsonify({'success': True, 'data': result})


@scraping_bp.route('/project/<int:project_id>/logs', methods=['GET'])
def get_project_logs(project_id):
    logs = ScrapeLog.query.join(ScrapeJob).filter(ScrapeJob.project_id == project_id).order_by(ScrapeLog.start_time.desc()).all()
    return jsonify({'success': True, 'data': [log.to_dict() for log in logs]})
