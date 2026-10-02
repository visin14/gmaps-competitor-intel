import json
from collections import defaultdict, Counter
from datetime import datetime
from models import db, Post, Competitor, TrendAnalysis


def calculate_trends(project_id: int) -> list:
    """Recompute topic trends for a project.

    Percentage = share of the project's competitors that use the topic
    (e.g. 25 of 50 competitors -> 50%), occurrence = number of posts on the topic.
    """
    total_competitors = Competitor.query.filter_by(project_id=project_id).count()
    posts = Post.query.filter(Post.project_id == project_id, Post.ai_main_topic.isnot(None)).all()

    topic_counts = defaultdict(int)
    topic_competitors = defaultdict(set)
    for p in posts:
        topic_counts[p.ai_main_topic] += 1
        topic_competitors[p.ai_main_topic].add(p.competitor_id)

    TrendAnalysis.query.filter_by(project_id=project_id).delete()

    new_trends = []
    for topic, count in topic_counts.items():
        comp_count = len(topic_competitors[topic])
        trend = TrendAnalysis(
            project_id=project_id,
            topic=topic,
            occurrence_count=count,
            competitor_count=comp_count,
            total_competitors=total_competitors,
            percentage=(comp_count / total_competitors * 100) if total_competitors else 0,
            last_calculated=datetime.utcnow(),
        )
        db.session.add(trend)
        new_trends.append(trend)
    db.session.commit()
    return sorted(new_trends, key=lambda t: t.occurrence_count, reverse=True)


def competitor_patterns(project_id: int) -> list:
    """Per-competitor publishing patterns: volume, cadence, top topics, CTAs and offer usage."""
    competitors = Competitor.query.filter_by(project_id=project_id).all()
    result = []
    for c in competitors:
        posts = Post.query.filter_by(competitor_id=c.id).all()
        topics = Counter(p.ai_main_topic for p in posts if p.ai_main_topic)
        ctas = Counter((p.ai_cta or p.call_to_action or '').strip().lower() for p in posts if (p.ai_cta or p.call_to_action))
        offers = sum(1 for p in posts if p.ai_offer_pattern and p.ai_offer_pattern.strip().upper() != 'N/A')
        dates = []
        for p in posts:
            try:
                dates.append(datetime.strptime((p.published_date or '')[:10], '%Y-%m-%d'))
            except ValueError:
                pass
        per_week = None
        if len(dates) >= 2:
            span_days = max((max(dates) - min(dates)).days, 1)
            per_week = round(len(dates) / span_days * 7, 2)
        result.append({
            'competitor_id': c.id,
            'competitor_name': c.name,
            'total_posts': len(posts),
            'posts_per_week': per_week,
            'top_topics': [{'topic': t, 'count': n} for t, n in topics.most_common(3)],
            'top_cta': ctas.most_common(1)[0][0] if ctas else None,
            'offer_share': round(offers / len(posts) * 100) if posts else 0,
            'last_post_date': max(dates).strftime('%Y-%m-%d') if dates else None,
        })
    return result


def top_keywords(project_id: int, limit: int = 20) -> list:
    counts = Counter()
    for p in Post.query.filter(Post.project_id == project_id, Post.ai_keywords.isnot(None)).all():
        try:
            for kw in json.loads(p.ai_keywords) or []:
                if isinstance(kw, str) and kw.strip():
                    counts[kw.lower().strip()] += 1
        except (ValueError, TypeError):
            pass
    return [{'keyword': k, 'count': v} for k, v in counts.most_common(limit)]
