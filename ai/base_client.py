import json, logging, re, time

TOPIC_HINTS = ('Hair Care Tips, Festival Offer, Before/After Transformation, New Service/Product, '
               'Appointment Availability, Bridal Package, Hair Color Trends, Keratin Treatment, '
               'Seasonal Discount, Staff Spotlight, General')


def extract_json(text):
    """Pull a JSON object/array out of a model reply (handles ``` fences and chatter)."""
    if not text:
        return None
    text = text.strip()
    candidates = []
    fenced = re.search(r'```(?:json)?\s*(.*?)\s*```', text, re.DOTALL)
    if fenced:
        candidates.append(fenced.group(1))
    candidates.append(text)
    for cand in candidates:
        try:
            return json.loads(cand)
        except ValueError:
            pass
        starts = [i for i in (cand.find('['), cand.find('{')) if i != -1]
        if not starts:
            continue
        start = min(starts)
        closer = ']' if cand[start] == '[' else '}'
        end = cand.rfind(closer)
        if end > start:
            try:
                return json.loads(cand[start:end + 1])
            except ValueError:
                continue
    return None


class BaseAIClient:
    """Shared prompts, retry and parsing. Subclasses only implement `_generate`."""
    provider = 'base'
    RETRY_DELAYS = (2, 6)

    def __init__(self):
        self.last_error = None

    def _generate(self, prompt: str) -> str:
        raise NotImplementedError

    def _on_error(self, exc: Exception) -> bool:
        """Return True if the client repaired itself (e.g. switched model) and a retry makes sense."""
        return False

    def _call(self, prompt: str):
        self.last_error = None
        attempt, repairs = 0, 0
        while attempt <= len(self.RETRY_DELAYS) and repairs < 12:
            try:
                text = self._generate(prompt)
                if text:
                    return text
                self.last_error = 'empty response'
            except Exception as exc:
                self.last_error = f'{type(exc).__name__}: {exc}'[:300]
                logging.error('%s call failed: %s', self.provider, self.last_error)
                if self._on_error(exc):
                    repairs += 1   # switched model: retry immediately without using up a retry
                    continue
            if attempt < len(self.RETRY_DELAYS):
                time.sleep(self.RETRY_DELAYS[attempt])
            attempt += 1
        return None

    def analyze_post(self, post_text: str):
        prompt = f'''You are a marketing analyst studying Google Maps business updates (posts).

Analyze this post and return ONLY a JSON object with exactly these keys:
{{
  "main_topic": "prefer one of: {TOPIC_HINTS}; otherwise a short 2-4 word topic",
  "sub_topic": "specific sub-topic in 3-5 words",
  "keywords": ["3 to 6 relevant keywords"],
  "content_type": "one of: Promotional, Educational, Engagement, Seasonal, Announcement",
  "call_to_action": "the call to action in the post, or empty string",
  "offer_pattern": "the discount/offer pattern mentioned (e.g. '20% off', 'free consultation') or N/A"
}}

Post text:
{post_text}'''
        result = extract_json(self._call(prompt))
        return result if isinstance(result, dict) else None

    def generate_ideas(self, count: int, ctx: dict):
        trends = ', '.join(f'{t["topic"]} ({t["percentage"]:.0f}% of competitors)' for t in ctx.get('trends', [])[:10]) \
            or 'no trend data yet'
        samples = '\n'.join(f'- {s}' for s in ctx.get('sample_posts', [])[:6]) or '- none collected yet'
        avoid = '\n'.join(f'- {a}' for a in ctx.get('avoid', [])[-40:]) or '- none'
        prompt = f'''You are a Google Maps marketing strategist for "{ctx.get("project_name")}", a {ctx.get("industry")} business.

Competitor research for this project:
- Topics competitors post about most: {trends}
- Example competitor updates:
{samples}

Write {count} NEW Google Maps update posts for this business, informed by the research above
(cover popular topics but with a fresh angle; do not copy competitor wording).

Do NOT repeat or closely paraphrase any of these previously generated ideas:
{avoid}

Return ONLY a JSON array of exactly {count} objects, each with:
{{
  "topic": "short unique topic name",
  "update_copy": "complete, ready-to-publish Google Maps post of 3-5 sentences, warm tone, a few emojis",
  "keywords": ["3-5 keywords"],
  "call_to_action": "specific call to action",
  "image_concept": "description of the ideal photo/graphic for this post"
}}'''
        result = extract_json(self._call(prompt))
        if isinstance(result, dict):
            for key in ('ideas', 'posts', 'updates'):
                if isinstance(result.get(key), list):
                    return result[key]
        return result if isinstance(result, list) else None

    def summarize_trends(self, trends_data: list) -> str:
        topics_str = '\n'.join(f'- {t["topic"]}: {t["percentage"]:.0f}% ({t["occurrence_count"]} posts)' for t in trends_data[:10])
        return self._call(f'Summarize these Google Maps content trends for a local business in 2 short paragraphs:\n{topics_str}') \
            or 'Unable to generate summary.'
