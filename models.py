from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import json

db = SQLAlchemy()

class Project(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    own_profile_name = db.Column(db.String(255), nullable=True)
    own_profile_url = db.Column(db.String(2048), nullable=True)
    description = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'own_profile_name': self.own_profile_name,
            'own_profile_url': self.own_profile_url,
            'description': self.description,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

class Competitor(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.Integer, db.ForeignKey('project.id'), nullable=False)
    name = db.Column(db.String(255), nullable=False)
    gmaps_url = db.Column(db.String(2048), nullable=False)
    notes = db.Column(db.Text, nullable=True)
    added_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_scraped_at = db.Column(db.DateTime, nullable=True)
    scrape_status = db.Column(db.String(50), default='idle')
    total_posts = db.Column(db.Integer, default=0)

    def to_dict(self):
        return {
            'id': self.id,
            'project_id': self.project_id,
            'name': self.name,
            'gmaps_url': self.gmaps_url,
            'google_maps_url': self.gmaps_url,  # name used by the frontend
            'notes': self.notes,
            'added_at': self.added_at.isoformat() if self.added_at else None,
            'last_scraped_at': self.last_scraped_at.isoformat() if self.last_scraped_at else None,
            'scrape_status': self.scrape_status,
            'total_posts': self.total_posts
        }

class Keyword(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.Integer, db.ForeignKey('project.id'), nullable=False)
    keyword = db.Column(db.String(255), nullable=False)
    added_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'project_id': self.project_id,
            'keyword': self.keyword,
            'added_at': self.added_at.isoformat() if self.added_at else None
        }

class Post(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.Integer, db.ForeignKey('project.id'), nullable=False)
    competitor_id = db.Column(db.Integer, db.ForeignKey('competitor.id'), nullable=False)
    competitor_name = db.Column(db.String(255), nullable=True)
    post_url = db.Column(db.String(2048), nullable=True)
    post_text = db.Column(db.Text, nullable=True)
    published_date = db.Column(db.String(255), nullable=True)
    images = db.Column(db.Text, nullable=True) # JSON string
    call_to_action = db.Column(db.String(255), nullable=True)
    detected_keywords = db.Column(db.Text, nullable=True)
    detected_topic = db.Column(db.String(255), nullable=True)
    source_url = db.Column(db.String(2048), nullable=True)
    fingerprint = db.Column(db.String(64), unique=True, index=True, nullable=False)
    scrape_date = db.Column(db.DateTime, default=datetime.utcnow)
    scrape_job_id = db.Column(db.Integer, db.ForeignKey('scrape_job.id'), nullable=True)
    ai_analyzed = db.Column(db.Boolean, default=False)
    ai_main_topic = db.Column(db.String(255), nullable=True)
    ai_sub_topic = db.Column(db.String(255), nullable=True)
    ai_content_type = db.Column(db.String(255), nullable=True)
    ai_keywords = db.Column(db.Text, nullable=True)
    ai_cta = db.Column(db.String(255), nullable=True)
    ai_offer_pattern = db.Column(db.String(255), nullable=True)
    ai_raw = db.Column(db.Text, nullable=True)

    def to_dict(self):
        d = {
            'id': self.id,
            'project_id': self.project_id,
            'competitor_id': self.competitor_id,
            'competitor_name': self.competitor_name,
            'post_url': self.post_url,
            'post_text': self.post_text,
            'published_date': self.published_date,
            'call_to_action': self.call_to_action,
            'detected_keywords': self.detected_keywords,
            'detected_topic': self.detected_topic,
            'source_url': self.source_url,
            'fingerprint': self.fingerprint,
            'scrape_date': self.scrape_date.isoformat() if self.scrape_date else None,
            'scrape_job_id': self.scrape_job_id,
            'ai_analyzed': self.ai_analyzed,
            'ai_main_topic': self.ai_main_topic,
            'ai_sub_topic': self.ai_sub_topic,
            'ai_content_type': self.ai_content_type,
            'ai_cta': self.ai_cta,
            'ai_offer_pattern': self.ai_offer_pattern,
            'ai_raw': self.ai_raw
        }
        try:
            d['images'] = json.loads(self.images) if self.images else []
        except:
            d['images'] = []
        try:
            d['ai_keywords'] = json.loads(self.ai_keywords) if self.ai_keywords else []
        except:
            d['ai_keywords'] = []
        return d

class ScrapeJob(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.Integer, db.ForeignKey('project.id'), nullable=False)
    started_at = db.Column(db.DateTime, default=datetime.utcnow)
    ended_at = db.Column(db.DateTime, nullable=True)
    status = db.Column(db.String(50), default='running')
    captcha_required = db.Column(db.Boolean, default=False)
    total_competitors = db.Column(db.Integer, default=0)
    processed_competitors = db.Column(db.Integer, default=0)

    def to_dict(self):
        return {
            'id': self.id,
            'project_id': self.project_id,
            'started_at': self.started_at.isoformat() if self.started_at else None,
            'ended_at': self.ended_at.isoformat() if self.ended_at else None,
            'status': self.status,
            'captcha_required': self.captcha_required,
            'total_competitors': self.total_competitors,
            'processed_competitors': self.processed_competitors
        }

class ScrapeLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    job_id = db.Column(db.Integer, db.ForeignKey('scrape_job.id'), nullable=False)
    competitor_id = db.Column(db.Integer, db.ForeignKey('competitor.id'), nullable=True)
    competitor_name = db.Column(db.String(255), nullable=True)
    start_time = db.Column(db.DateTime, default=datetime.utcnow)
    end_time = db.Column(db.DateTime, nullable=True)
    posts_found = db.Column(db.Integer, default=0)
    new_posts = db.Column(db.Integer, default=0)
    duplicates_skipped = db.Column(db.Integer, default=0)
    images_downloaded = db.Column(db.Integer, default=0)
    status = db.Column(db.String(50), nullable=True)
    error_info = db.Column(db.Text, nullable=True)
    captcha_encountered = db.Column(db.Boolean, default=False)
    manual_intervention = db.Column(db.Boolean, default=False)

    def to_dict(self):
        return {
            'id': self.id,
            'job_id': self.job_id,
            'competitor_id': self.competitor_id,
            'competitor_name': self.competitor_name,
            'start_time': self.start_time.isoformat() if self.start_time else None,
            'end_time': self.end_time.isoformat() if self.end_time else None,
            'posts_found': self.posts_found,
            'new_posts': self.new_posts,
            'duplicates_skipped': self.duplicates_skipped,
            'images_downloaded': self.images_downloaded,
            'status': self.status,
            'error_info': self.error_info,
            'captcha_encountered': self.captcha_encountered,
            'manual_intervention': self.manual_intervention
        }

class GeneratedIdea(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.Integer, db.ForeignKey('project.id'), nullable=False)
    topic = db.Column(db.String(255), nullable=True)
    update_copy = db.Column(db.Text, nullable=True)
    keywords = db.Column(db.Text, nullable=True) # JSON
    call_to_action = db.Column(db.String(255), nullable=True)
    image_concept = db.Column(db.Text, nullable=True)
    ai_provider = db.Column(db.String(50), default='gemini')
    generated_at = db.Column(db.DateTime, default=datetime.utcnow)
    fingerprint = db.Column(db.String(64), unique=True, index=True, nullable=False)
    is_used = db.Column(db.Boolean, default=False)

    def to_dict(self):
        d = {
            'id': self.id,
            'project_id': self.project_id,
            'topic': self.topic,
            'update_copy': self.update_copy,
            'call_to_action': self.call_to_action,
            'image_concept': self.image_concept,
            'ai_provider': self.ai_provider,
            'generated_at': self.generated_at.isoformat() if self.generated_at else None,
            'fingerprint': self.fingerprint,
            'is_used': self.is_used
        }
        try:
            d['keywords'] = json.loads(self.keywords) if self.keywords else []
        except:
            d['keywords'] = []
        return d

class TrendAnalysis(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.Integer, db.ForeignKey('project.id'), nullable=False)
    topic = db.Column(db.String(255), nullable=True)
    occurrence_count = db.Column(db.Integer, default=0)
    competitor_count = db.Column(db.Integer, default=0)
    total_competitors = db.Column(db.Integer, default=0)
    percentage = db.Column(db.Float, default=0.0)
    last_calculated = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'project_id': self.project_id,
            'topic': self.topic,
            'occurrence_count': self.occurrence_count,
            'competitor_count': self.competitor_count,
            'total_competitors': self.total_competitors,
            'percentage': self.percentage,
            'last_calculated': self.last_calculated.isoformat() if self.last_calculated else None
        }
