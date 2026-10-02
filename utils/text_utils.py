import re
from datetime import datetime, timedelta

# Keyword heuristics used when no AI provider is reachable, and to fill the
# "detected topic / keywords" fields at scrape time.
TOPIC_MAP = {
    'Hair Care Tips': ['hair care', 'conditioning', 'damage', 'moistur', 'protein', 'oil massage', 'hair spa'],
    'Festival Offer': ['festival', 'navratri', 'diwali', 'christmas', 'holi', 'eid', 'garba', 'raksha'],
    'Before/After Transformation': ['transformation', 'before and after', 'before & after', 'makeover'],
    'New Service/Product': ['new service', 'launch', 'introducing', 'excited to announce', 'now available'],
    'Appointment Availability': ['appointment', 'slot', 'booking', 'available', 'book now', 'walk-in', 'walk in'],
    'Bridal Package': ['bridal', 'bride', 'wedding', 'shaadi'],
    'Hair Color Trends': ['color', 'colour', 'balayage', 'highlights', 'toner', 'blonde'],
    'Keratin Treatment': ['keratin', 'smoothing', 'frizz', 'brazilian blowout'],
    'Seasonal Discount': ['sale', 'discount', '% off', 'flat', 'offer', 'deal'],
    'Staff Spotlight': ['meet ', 'our team', 'stylist', 'specialist', 'expert'],
}

KEYWORD_VOCAB = ['hair', 'salon', 'treatment', 'booking', 'offer', 'color', 'style', 'bridal', 'keratin',
                 'facial', 'spa', 'makeup', 'discount', 'appointment', 'skin', 'nail']

CTA_WORDS = ['book', 'call', 'learn more', 'order', 'buy', 'sign up', 'reserve', 'get offer', 'visit', 'whatsapp', 'enquire']


def detect_topic(text: str) -> str:
    text = (text or '').lower()
    for topic, words in TOPIC_MAP.items():
        if any(w in text for w in words):
            return topic
    return 'General'


def detect_keywords(text: str, limit: int = 6) -> list:
    text = (text or '').lower()
    return [w for w in KEYWORD_VOCAB if w in text][:limit]


_REL = re.compile(r'\b(?:(\d+)|an?|one)\s+(minute|hour|day|week|month|year)s?\s+ago\b', re.I)
REL_DATE_RE = _REL


def parse_relative_date(text: str, now: datetime = None):
    """'3 weeks ago' -> 'YYYY-MM-DD'. Returns None if the text is not a relative date."""
    if not text:
        return None
    now = now or datetime.utcnow()
    m = _REL.search(text)
    if m:
        n = int(m.group(1)) if m.group(1) else 1
        unit = m.group(2).lower()
        days = {'minute': 0, 'hour': 0, 'day': n, 'week': 7 * n, 'month': 30 * n, 'year': 365 * n}[unit]
        return (now - timedelta(days=days)).strftime('%Y-%m-%d')
    low = text.lower()
    if 'yesterday' in low:
        return (now - timedelta(days=1)).strftime('%Y-%m-%d')
    if 'today' in low or 'just now' in low:
        return now.strftime('%Y-%m-%d')
    for fmt in ('%b %d, %Y', '%B %d, %Y', '%d %b %Y', '%d %B %Y', '%Y-%m-%d'):
        try:
            return datetime.strptime(text.strip(), fmt).strftime('%Y-%m-%d')
        except ValueError:
            continue
    return None
