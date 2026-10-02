"""Pure HTML parsing for the Google Maps "Updates" panel (no Selenium needed, so it is unit-testable).

Google changes its generated class names often, so extraction does not rely on them:
1. try a list of explicit card selectors (edit CARD_SELECTORS if Google changes the markup);
2. otherwise fall back to a structural heuristic: the innermost element that contains a
   relative date ("2 weeks ago") plus a block of text.
"""
import re
from datetime import datetime
from bs4 import BeautifulSoup
from utils.text_utils import REL_DATE_RE, CTA_WORDS, parse_relative_date

CARD_SELECTORS = ['div[data-update-id]', 'div[data-post-id]', 'div[role="article"]', 'div.section-update']
UI_NOISE = {'share', 'like', 'more', 'report', 'copy link', 'open', 'close', 'see more', 'read more', 'updates', 'overview', 'reviews', 'about'}
SMALL_IMG = re.compile(r'=[sw]\d{1,2}(?:-|$)|/a-/|/a/')  # avatars / tiny thumbnails


def _lines(el):
    return [t.strip() for t in el.get_text('\n', strip=True).split('\n') if t.strip()]


def _heuristic_cards(soup):
    def qualifies(el):
        text = el.get_text(' ', strip=True)
        return len(text) >= 40 and REL_DATE_RE.search(text) is not None

    candidates = [d for d in soup.find_all('div') if qualifies(d)]
    # keep the innermost qualifying elements (those with no qualifying descendant div)
    leaves = [d for d in candidates if not any(qualifies(c) for c in d.find_all('div', recursive=True) if c is not d)]
    # Drop leaves wrapped by a bigger leaf group is unnecessary: leaves have no qualifying descendants.
    return leaves


def _parse_card(card, now=None):
    lines = _lines(card)
    date_text = next((l for l in lines if REL_DATE_RE.fullmatch(l) or REL_DATE_RE.search(l) and len(l) < 30), None)

    cta = None
    for el in card.find_all(['a', 'button']):
        label = (el.get('aria-label') or el.get_text(' ', strip=True) or '').strip()
        if label and len(label) < 40 and any(w in label.lower() for w in CTA_WORDS):
            cta = label
            break

    noise = {l.lower() for l in lines if l.lower() in UI_NOISE}
    body = [l for l in lines
            if l != date_text and l.lower() not in noise and l != cta and len(l) > 1]
    text = '\n'.join(body).strip()

    images = []
    for img in card.find_all('img'):
        src = img.get('src') or img.get('data-src') or ''
        if src.startswith('http') and 'googleusercontent' in src and not SMALL_IMG.search(src) and src not in images:
            images.append(src)

    url = None
    for a in card.find_all('a', href=True):
        href = a['href']
        if href.startswith('http') and ('/posts/' in href or 'post' in href.lower()):
            url = href
            break

    return {
        'text': text,
        'date': parse_relative_date(date_text, now) if date_text else None,
        'date_text': date_text,
        'images': images[:6],
        'cta': cta,
        'url': url,
    }


def parse_updates_html(html: str, now: datetime = None) -> list:
    soup = BeautifulSoup(html, 'html.parser')
    cards = []
    for sel in CARD_SELECTORS:
        cards = soup.select(sel)
        if cards:
            break
    if not cards:
        cards = _heuristic_cards(soup)

    posts, seen = [], set()
    for card in cards:
        parsed = _parse_card(card, now)
        key = parsed['text'][:120]
        if len(parsed['text']) >= 10 and key not in seen:
            seen.add(key)
            posts.append(parsed)
    return posts
