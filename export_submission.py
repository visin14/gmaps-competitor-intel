"""Export a project's data into submission/ (CSV + JSON) for the assignment hand-in.

    python export_submission.py                  # export project 1 from the local database
    python export_submission.py --project-id 2
    python export_submission.py --generate 6     # first generate 6 NEW ideas with the configured AI providers

Every generated idea keeps its `ai_provider` (gemini / grok / fallback / demo) so nothing is mislabeled.
"""
import argparse, csv, json, os
from app import app
from models import Project, Competitor, Post, ScrapeLog, ScrapeJob, GeneratedIdea, TrendAnalysis
from utils.trends import competitor_patterns, top_keywords

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'submission')


def write_csv(name, rows, fields):
    with open(os.path.join(OUT, name), 'w', newline='', encoding='utf-8-sig') as f:
        w = csv.DictWriter(f, fieldnames=fields, extrasaction='ignore')
        w.writeheader()
        w.writerows(rows)
    print(f'  {name}: {len(rows)} rows')


def write_json(name, data):
    with open(os.path.join(OUT, name), 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    print(f'  {name}')


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--project-id', type=int, default=1)
    parser.add_argument('--generate', type=int, default=0, help='generate N new ideas with the AI providers first')
    args = parser.parse_args()
    pid = args.project_id
    os.makedirs(OUT, exist_ok=True)

    with app.app_context():
        project = Project.query.get(pid)
        if not project:
            raise SystemExit(f'Project {pid} not found')

        if args.generate:
            from ai.analyzer import generate_ideas_for_project
            result = generate_ideas_for_project(pid, args.generate, app)
            print(f'Generated {len(result["ideas"])} ideas via {result["provider"]}; warnings: {result["warnings"]}')

        print(f'Exporting "{project.name}" to {OUT}')
        comps = Competitor.query.filter_by(project_id=pid).all()
        write_csv('competitors.csv', [{**c.to_dict(), 'post_count': Post.query.filter_by(competitor_id=c.id).count()} for c in comps],
                  ['id', 'name', 'gmaps_url', 'notes', 'scrape_status', 'last_scraped_at', 'total_posts'])

        posts = Post.query.filter_by(project_id=pid).order_by(Post.id).all()
        write_csv('collected_posts.csv', [{**p.to_dict(), 'images': ' | '.join(p.to_dict()['images'])} for p in posts],
                  ['id', 'competitor_name', 'post_url', 'source_url', 'post_text', 'published_date', 'images',
                   'call_to_action', 'detected_topic', 'detected_keywords', 'scrape_date', 'scrape_job_id', 'fingerprint'])

        write_csv('ai_analysis.csv', [{**p.to_dict(), 'ai_keywords': ', '.join(p.to_dict()['ai_keywords'])} for p in posts if p.ai_analyzed],
                  ['id', 'competitor_name', 'ai_main_topic', 'ai_sub_topic', 'ai_content_type', 'ai_keywords', 'ai_cta', 'ai_offer_pattern'])

        trends = TrendAnalysis.query.filter_by(project_id=pid).order_by(TrendAnalysis.occurrence_count.desc()).all()
        trend_rows = [{**t.to_dict(), 'competitors_using': f'{t.competitor_count} of {t.total_competitors}',
                       'percentage': round(t.percentage, 1)} for t in trends]
        write_csv('trends.csv', trend_rows, ['topic', 'occurrence_count', 'competitors_using', 'percentage'])
        write_json('top_keywords.json', top_keywords(pid, 20))
        write_json('competitor_publishing_patterns.json', competitor_patterns(pid))

        ideas = GeneratedIdea.query.filter_by(project_id=pid).order_by(GeneratedIdea.generated_at).all()
        write_csv('generated_updates.csv', [{**i.to_dict(), 'keywords': ', '.join(i.to_dict()['keywords'])} for i in ideas],
                  ['id', 'topic', 'update_copy', 'keywords', 'call_to_action', 'image_concept', 'ai_provider', 'generated_at'])

        jobs = [j.id for j in ScrapeJob.query.filter_by(project_id=pid).all()]
        logs = ScrapeLog.query.filter(ScrapeLog.job_id.in_(jobs)).order_by(ScrapeLog.id).all() if jobs else []
        write_csv('scrape_logs.csv', [l.to_dict() for l in logs],
                  ['job_id', 'competitor_name', 'start_time', 'end_time', 'posts_found', 'new_posts', 'duplicates_skipped',
                   'images_downloaded', 'status', 'captcha_encountered', 'manual_intervention', 'error_info'])

        by_provider = {}
        for i in ideas:
            by_provider[i.ai_provider] = by_provider.get(i.ai_provider, 0) + 1
        print('Generated updates by source:', by_provider)


if __name__ == '__main__':
    main()
