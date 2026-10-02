import os, json, logging, re, difflib
from models import db, Post, GeneratedIdea, TrendAnalysis, Project
from utils.fingerprint import compute_idea_fingerprint
from utils.text_utils import detect_topic, detect_keywords
from utils.trends import calculate_trends

PROVIDER_CLASSES = {
    'gemini': ('ai.gemini_client', 'GeminiClient', 'GEMINI_API_KEY'),
    'grok': ('ai.grok_client', 'GrokClient', 'GROK_API_KEY'),
}


def _real_key(value: str) -> bool:
    return bool(value) and not value.startswith('your_') and value != 'change-this'


def get_ai_clients() -> list:
    """All configured providers, in priority order (AI_PROVIDER_ORDER, default gemini,grok)."""
    order = [p.strip().lower() for p in os.environ.get('AI_PROVIDER_ORDER', 'gemini,grok').split(',') if p.strip()]
    clients = []
    for name in order:
        spec = PROVIDER_CLASSES.get(name)
        if not spec:
            continue
        module_name, class_name, env_key = spec
        key = os.environ.get(env_key, '')
        if not _real_key(key):
            continue
        try:
            module = __import__(module_name, fromlist=[class_name])
            clients.append(getattr(module, class_name)(key))
        except Exception as e:
            logging.error('%s init failed: %s', name, e)
    return clients


def get_ai_client():
    """Backwards compatible helper: first available (client, provider_name)."""
    clients = get_ai_clients()
    return (clients[0], clients[0].provider) if clients else (None, None)


def _first_success(clients, method, *args):
    """Call `method` on each provider in turn until one returns a usable result."""
    errors = []
    for client in clients:
        try:
            result = getattr(client, method)(*args)
        except Exception as e:
            errors.append(f'{client.provider}: {e}')
            continue
        if result:
            return result, client.provider, errors
        errors.append(f'{client.provider}: {client.last_error or "no usable response"}')
    return None, None, errors


def _short(value, limit=255):
    return (str(value) if value is not None else '')[:limit]


# ----------------------------------------------------------------------------- post analysis

def _apply_analysis(post, result: dict, provider: str):
    keywords = result.get('keywords') or []
    if not isinstance(keywords, list):
        keywords = [str(keywords)]
    post.ai_main_topic = _short(result.get('main_topic') or 'General')
    post.ai_sub_topic = _short(result.get('sub_topic'))
    post.ai_content_type = _short(result.get('content_type') or 'General')
    post.ai_keywords = json.dumps([str(k) for k in keywords][:8])
    post.ai_cta = _short(result.get('call_to_action'))
    post.ai_offer_pattern = _short(result.get('offer_pattern') or 'N/A')
    post.ai_raw = json.dumps({**result, 'provider': provider})
    post.ai_analyzed = True


def _fallback_analysis(post) -> dict:
    text = (post.post_text or '').lower()
    return {
        'main_topic': detect_topic(text),
        'sub_topic': '',
        'content_type': 'Promotional' if any(w in text for w in ('off', '%', 'free', 'discount', 'offer')) else 'Announcement',
        'keywords': detect_keywords(text, 5),
        'call_to_action': post.call_to_action or ('Book now' if 'book' in text else ''),
        'offer_pattern': 'Discount' if any(w in text for w in ('off', '%', 'free', 'discount')) else 'N/A',
    }


def analyze_post(post_id: int, app, clients=None):
    with app.app_context():
        post = db.session.get(Post, post_id)
        if not post:
            return None
        if clients is None:
            clients = get_ai_clients()
        result, provider, _ = _first_success(clients, 'analyze_post', post.post_text or '') if clients else (None, None, [])
        if isinstance(result, dict):
            _apply_analysis(post, result, provider)
        else:
            _apply_analysis(post, _fallback_analysis(post), 'fallback')
        db.session.commit()
        return post.to_dict()


def analyze_project(project_id: int, app):
    """Analyze every pending post, then refresh the project's trends."""
    with app.app_context():
        clients = get_ai_clients()
        pending_ids = [p.id for p in Post.query.filter_by(project_id=project_id, ai_analyzed=False).all()]
        for post_id in pending_ids:
            try:
                analyze_post(post_id, app, clients)
            except Exception as e:
                db.session.rollback()
                logging.error('Failed to analyze post %s: %s', post_id, e)
        try:
            calculate_trends(project_id)
        except Exception as e:
            db.session.rollback()
            logging.error('Trend calculation failed: %s', e)


# ----------------------------------------------------------------------------- idea generation

def _norm(text):
    return re.sub(r'[^a-z0-9 ]+', '', (text or '').lower()).strip()


def _tokens(text):
    return {w for w in _norm(text).split() if len(w) > 3}


def is_similar_idea(topic, copy, known, check_copy=True) -> bool:
    """True if (topic, copy) repeats or closely paraphrases anything in `known`."""
    t = _norm(topic)
    c = _tokens(copy) if check_copy else set()
    for known_topic, known_copy in known:
        kt = _norm(known_topic)
        if t and (t == kt or difflib.SequenceMatcher(None, t, kt).ratio() >= 0.85):
            return True
        kc = _tokens(known_copy) if check_copy else set()
        if c and kc and len(c & kc) / len(c | kc) >= 0.6:
            return True
    return False


DEFAULT_TOPICS = ['Hair Care Tips', 'Festival Offer', 'Before/After Transformation', 'New Service/Product',
                  'Appointment Availability', 'Bridal Package', 'Seasonal Discount', 'Staff Spotlight',
                  'Customer Testimonial', 'Loyalty Rewards', 'Referral Offer', 'Weekend Special']

# (label, copy template, call to action, image concept)
ANGLES = [
    ('Limited-Time Offer', '✨ {topic} at {business}! For a limited time, enjoy a special offer on {topic_lower}. Our experienced team will take care of you from start to finish. Slots fill quickly, so reserve yours today!', 'Book your slot now', 'Bright, welcoming photo of the service being performed with an offer badge'),
    ('Expert Tips', '💡 Quick tip from the {business} team on {topic_lower}: small, regular habits make the biggest difference. Drop in and our specialists will build a plan that suits you. Questions? We are happy to help!', 'Visit us for a free consultation', 'Clean infographic-style photo of an expert giving advice to a client'),
    ('Behind the Scenes', '🎬 Ever wondered what goes into {topic_lower}? Take a peek behind the scenes at {business}. Every detail is done with care, premium products and a lot of passion. Come see it for yourself!', 'Walk in and see for yourself', 'Candid behind-the-scenes shot of the team at work'),
    ('Customer Favourite', '❤️ {topic} is one of our most-loved services at {business}, and our regulars keep coming back for it. Treat yourself this week and find out why. We would love to see you!', 'Call us to book', 'Happy client smiling after the service'),
    ('This Week Only', '📅 This week at {business}: {topic_lower} is the star of the show. Whether you are planning ahead or need something last minute, our doors are open. Get in touch and we will fit you in!', 'Message us on WhatsApp', 'Calendar-style graphic with the week highlighted and a salon interior in the background'),
    ('Bring a Friend', '👯 Bring a friend for {topic_lower} at {business} and make it a day to remember. Great company, great results and a little extra something for you both. Spots are limited, so plan your visit!', 'Book for two today', 'Two friends laughing together in the salon chairs'),
]


def _template_ideas(project, topics, known, needed):
    business = project.own_profile_name or project.name
    ideas = []
    for label, copy_tpl, cta, image in ANGLES:
        for topic in topics:
            if len(ideas) >= needed:
                return ideas
            title = f'{topic}: {label}'
            copy = copy_tpl.format(topic=topic, topic_lower=topic.lower(), business=business)
            # templates share boilerplate wording, so only the title is compared for them
            if is_similar_idea(title, copy, known + [(i['topic'], i['update_copy']) for i in ideas], check_copy=False):
                continue
            ideas.append({
                'topic': title, 'update_copy': copy,
                'keywords': [topic.lower(), label.lower(), (project.description or 'local business').split()[0].lower()],
                'call_to_action': cta, 'image_concept': image,
            })
    return ideas


def _industry(project) -> str:
    return (project.description or '').strip().rstrip('.') or 'local'


def generate_ideas_for_project(project_id: int, count: int, app):
    """Generate exactly `count` ideas where possible, never repeating earlier ones for this project.

    Returns {'ideas': [...], 'provider': str, 'requested': int, 'warnings': [...]} or None if the project is missing.
    """
    with app.app_context():
        project = db.session.get(Project, project_id)
        if not project:
            return None

        clients = get_ai_clients()
        trends = [t.to_dict() for t in TrendAnalysis.query.filter_by(project_id=project_id)
                  .order_by(TrendAnalysis.occurrence_count.desc()).limit(10).all()]
        samples = [(p.post_text or '')[:220] for p in Post.query.filter_by(project_id=project_id)
                   .order_by(Post.scrape_date.desc()).limit(6).all() if p.post_text]
        known = [(i.topic or '', i.update_copy or '') for i in GeneratedIdea.query.filter_by(project_id=project_id).all()]

        accepted, providers, warnings = [], set(), []

        def accept(raw_list, provider):
            for item in raw_list:
                if len(accepted) >= count:
                    break
                if not isinstance(item, dict):
                    continue
                topic, copy = _short(item.get('topic') or 'General'), item.get('update_copy') or ''
                if not copy.strip():
                    continue
                if is_similar_idea(topic, copy, known + [(a['topic'], a['update_copy']) for a in accepted]):
                    continue
                keywords = item.get('keywords') if isinstance(item.get('keywords'), list) else []
                accepted.append({'topic': topic, 'update_copy': copy, 'keywords': [str(k) for k in keywords],
                                 'call_to_action': _short(item.get('call_to_action')),
                                 'image_concept': item.get('image_concept') or '', 'ai_provider': provider})
                providers.add(provider)

        if not clients:
            warnings.append('No AI API key configured - used offline templates. Add GEMINI_API_KEY / GROK_API_KEY to .env for AI-written ideas.')
        for _ in range(5 if clients else 0):
            need = count - len(accepted)
            if need <= 0:
                break
            ctx = {
                'project_name': project.own_profile_name or project.name, 'industry': _industry(project),
                'trends': trends, 'sample_posts': samples,
                'avoid': [f'{t}: {c[:80]}' for t, c in known + [(a['topic'], a['update_copy']) for a in accepted]],
            }
            raw, provider, errors = _first_success(clients, 'generate_ideas', min(need + 2, 12), ctx)
            if not raw or not isinstance(raw, list):
                warnings.append('AI providers failed: ' + '; '.join(errors)[:300])
                break
            accept(raw, provider)

        if len(accepted) < count:
            topics = [t['topic'] for t in trends] or DEFAULT_TOPICS
            topics = topics + [t for t in DEFAULT_TOPICS if t not in topics]
            filler = _template_ideas(project, topics, known + [(a['topic'], a['update_copy']) for a in accepted], count - len(accepted))
            for item in filler:
                item['ai_provider'] = 'fallback'
            accepted.extend(filler)
            if clients and filler:
                warnings.append(f'AI returned fewer unique ideas than requested; {len(filler)} filled from offline templates.')

        saved = []
        for item in accepted:
            fp = compute_idea_fingerprint(item['topic'], item['update_copy'], project_id)
            if GeneratedIdea.query.filter_by(fingerprint=fp).first():
                continue
            idea = GeneratedIdea(project_id=project_id, topic=item['topic'], update_copy=item['update_copy'],
                                 keywords=json.dumps(item['keywords']), call_to_action=item['call_to_action'],
                                 image_concept=item['image_concept'], ai_provider=item['ai_provider'], fingerprint=fp)
            db.session.add(idea)
            saved.append(idea)
        db.session.commit()
        if len(saved) < count:
            warnings.append(f'Only {len(saved)} of {count} unique ideas could be produced.')

        provider = ', '.join(sorted({i.ai_provider for i in saved})) or 'none'
        return {'ideas': [i.to_dict() for i in saved], 'provider': provider, 'requested': count, 'warnings': warnings}
