import hashlib, re, uuid

def compute_fingerprint(post_url: str = None, post_text: str = None, competitor_id: int = None, project_id: int = None) -> str:
    """Stable identity for a scraped post.

    Prefers the post URL (scoped to the project so the same competitor can live in several
    projects), otherwise falls back to competitor + normalised text.
    """
    if post_url and len(post_url.strip()) > 10:
        raw = f'{project_id}::{post_url.strip().lower()}'
    elif post_text and competitor_id is not None:
        normalized = re.sub(r'\s+', ' ', post_text.lower().strip())[:500]
        raw = f'{competitor_id}::{normalized}'
    else:
        raw = str(uuid.uuid4())
    return hashlib.sha256(raw.encode('utf-8')).hexdigest()

def compute_idea_fingerprint(topic: str, update_copy: str, project_id: int = None) -> str:
    normalized_topic = (topic or '').lower().strip()
    normalized_copy = re.sub(r'\s+', ' ', (update_copy or '').lower().strip())[:200]
    raw = f'{project_id}::{normalized_topic}::{normalized_copy}'
    return hashlib.sha256(raw.encode('utf-8')).hexdigest()
