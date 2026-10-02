import json
from models import db, Project, Post, Competitor, GeneratedIdea
from datetime import datetime
from utils.seed_data import seed_data_for_app, create_demo_posts
from utils.demo_assets import make_demo_image, SAMPLE_IDEAS
from utils.fingerprint import compute_idea_fingerprint
from utils.text_utils import detect_topic, detect_keywords
from utils.trends import calculate_trends


def seed_data(app):
    with app.app_context():
        if Project.query.first() is None:
            seed_data_for_app(app)
        upgrade_demo_data(app)


def upgrade_demo_data(app):
    """Idempotently bring an older demo dataset up to date (images, source info, real trends, sample ideas)."""
    demo_posts = [p for p in Post.query.all() if p.ai_raw and '"dummy"' in p.ai_raw]
    if not demo_posts:
        return
    changed = False

    # Older demo data tied every topic to a single competitor (so every trend read "1 of 5"); regenerate it.
    topic_users = {}
    for p in demo_posts:
        topic_users.setdefault(p.ai_main_topic, set()).add(p.competitor_id)
    if all(len(users) == 1 for users in topic_users.values()):
        project_id = demo_posts[0].project_id
        project = db.session.get(Project, project_id)
        competitors = Competitor.query.filter_by(project_id=project_id).order_by(Competitor.id).all()
        for p in demo_posts:
            db.session.delete(p)
        db.session.flush()
        create_demo_posts(project, competitors, datetime.utcnow(), count=len(demo_posts))
        db.session.commit()
        demo_posts = [p for p in Post.query.filter_by(project_id=project_id).all() if p.ai_raw and '"dummy"' in p.ai_raw]
        changed = True
    comps = {c.id: c for c in Competitor.query.all()}
    for p in demo_posts:
        comp = comps.get(p.competitor_id)
        if not p.source_url and comp:
            p.source_url, changed = comp.gmaps_url, True
        if not p.detected_topic:
            p.detected_topic, p.detected_keywords, changed = detect_topic(p.post_text), json.dumps(detect_keywords(p.post_text)), True
        if (not p.images or p.images == '[]') and comp:
            p.images = json.dumps([make_demo_image(app, p.project_id, p.competitor_id, comp.name, p.ai_main_topic or 'Update', p.post_text or str(p.id))])
            changed = True

    # replace the old placeholder ideas ("A nice photo") with realistic samples
    placeholders = GeneratedIdea.query.filter_by(image_concept='A nice photo').all()
    if placeholders:
        project_id = placeholders[0].project_id
        for idea in placeholders:
            db.session.delete(idea)
        for topic, copy, kws, cta, image in SAMPLE_IDEAS:
            db.session.add(GeneratedIdea(project_id=project_id, topic=topic, update_copy=copy, keywords=json.dumps(kws),
                                         call_to_action=cta, image_concept=image, ai_provider='demo',
                                         fingerprint=compute_idea_fingerprint(topic, copy, project_id)))
        changed = True
    if changed:
        db.session.commit()
        for project_id in {p.project_id for p in demo_posts}:
            calculate_trends(project_id)
