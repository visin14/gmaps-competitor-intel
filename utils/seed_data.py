import json, random, hashlib, uuid
from datetime import datetime, timedelta
from models import db, Project, Competitor, Keyword, Post, ScrapeJob, ScrapeLog, GeneratedIdea, TrendAnalysis
from utils.fingerprint import compute_fingerprint, compute_idea_fingerprint

def seed_data_for_app(app):
    with app.app_context():
        # Create Project
        project = Project(
            name='Luxe Salon & Spa',
            own_profile_name='Luxe Salon Kharghar',
            own_profile_url='https://maps.google.com/maps?cid=5551234567890',
            description='Premium salon offering hair and skin services.'
        )
        db.session.add(project)
        db.session.commit()
        
        # Create Competitors
        comps = [
            {'name': 'Naturals Salon', 'url': 'https://maps.google.com/maps?cid=1001'},
            {'name': 'Enrich Salon', 'url': 'https://maps.google.com/maps?cid=1002'},
            {'name': 'Jawed Habib', 'url': 'https://maps.google.com/maps?cid=1003'},
            {'name': 'Looks Salon', 'url': 'https://maps.google.com/maps?cid=1004'},
            {'name': 'Green Trends', 'url': 'https://maps.google.com/maps?cid=1005'}
        ]
        competitors = []
        for c in comps:
            comp = Competitor(project_id=project.id, name=c['name'], gmaps_url=c['url'], total_posts=11, last_scraped_at=datetime.utcnow(), scrape_status='done')
            db.session.add(comp)
            competitors.append(comp)
        db.session.commit()
        
        # Create Keywords
        for k in ['hair salon', 'bridal makeup', 'keratin treatment']:
            db.session.add(Keyword(project_id=project.id, keyword=k))
        db.session.commit()
        
        # Create Posts
        topics = [
            ('Hair Care Tips', 'Monsoon hair woes? Our expert stylists recommend a weekly oil massage and protein treatment to keep your locks healthy. Visit us this week and enjoy 15% off all conditioning services. Call to book your slot!'),
            ('Festival Offer', 'Navratri is here! Get festival-ready with our special Garba Glam package — includes blow-dry, styling & nail art at just ₹999. Limited slots available. Book now!'),
            ('Before/After Transformation', 'Check out this incredible hair transformation! Our client came in with damaged, frizzy hair and left with smooth, shiny, healthy locks. All thanks to our signature Brazilian Blowout treatment. Book your transformation today!'),
            ('New Service/Product', 'We\'re excited to announce our new Scalp Micropigmentation service! Perfect for those experiencing hair thinning or baldness. Consult our certified specialists. First 10 bookings get a complimentary scalp analysis!'),
            ('Appointment Availability', 'Good news — slots are now open for this weekend! Whether you need a quick trim, full color, or a bridal trial, we have you covered. Book via link in bio or call us directly.'),
            ('Bridal Package', 'Our Dream Bridal Package includes pre-bridal facials, hair spa, mehendi, makeup trial and final day makeup. Packages starting at ₹19,999. Book your bridal consultation today!'),
            ('Hair Color Trends', 'Balayage is trending this season and we\'re obsessed! Our expert colorists craft custom balayage looks tailored to your skin tone. Get a free consultation this week. Limited slots!'),
            ('Keratin Treatment', '90-day keratin smoothing treatment now available at our salon! Say goodbye to frizz and hello to glossy, manageable hair. Treatment time: 2.5 hours. Book your slot this week!'),
            ('Seasonal Discount', 'End of season sale is LIVE! Get flat 30% off on all hair services this week only. Offer valid till Sunday. Don\'t miss out — call to book!'),
            ('Staff Spotlight', 'Meet Priya, our star hair colorist with 8 years of experience! She specializes in global color, highlights, and creative fashion colors. Book with Priya this week and get a complimentary toner!')
        ]
        
        base_time = datetime.utcnow()
        for i in range(55):
            comp = competitors[i % 5]
            topic_name, template_text = topics[i % 10]
            
            # Make text slightly unique
            text = template_text.replace('!', f'! #{i:02d}', 1)
            fp = compute_fingerprint(post_text=text, competitor_id=comp.id)
            
            post = Post(
                project_id=project.id,
                competitor_id=comp.id,
                competitor_name=comp.name,
                post_text=text,
                published_date=(base_time - timedelta(days=i)).strftime('%Y-%m-%d'),
                images=json.dumps([]),
                call_to_action='Book now' if i % 2 == 0 else 'Learn more',
                fingerprint=fp,
                scrape_date=base_time - timedelta(days=i%5),
                ai_analyzed=True,
                ai_main_topic=topic_name,
                ai_sub_topic='General',
                ai_content_type='Promotional',
                ai_keywords=json.dumps(['salon', 'hair', 'beauty', topic_name.lower()]),
                ai_cta='Book appointment',
                ai_offer_pattern='Discount' if 'off' in text.lower() or '₹' in text else 'N/A',
                ai_raw=json.dumps({'dummy': True})
            )
            db.session.add(post)
        db.session.commit()
        
        # Scrape Jobs and Logs
        job1 = ScrapeJob(project_id=project.id, started_at=base_time - timedelta(days=2), ended_at=base_time - timedelta(days=2), status='done', total_competitors=5, processed_competitors=5)
        job2 = ScrapeJob(project_id=project.id, started_at=base_time, ended_at=base_time, status='done', total_competitors=5, processed_competitors=5)
        db.session.add(job1)
        db.session.add(job2)
        db.session.commit()
        
        for job in [job1, job2]:
            for comp in competitors:
                log = ScrapeLog(
                    job_id=job.id,
                    competitor_id=comp.id,
                    competitor_name=comp.name,
                    start_time=job.started_at,
                    end_time=job.ended_at,
                    posts_found=11,
                    new_posts=11 if job == job1 else 0,
                    duplicates_skipped=0 if job == job1 else 11,
                    status='success'
                )
                db.session.add(log)
        db.session.commit()
        
        # Generated Ideas
        for i in range(5):
            topic_name = topics[i][0]
            copy = topics[i][1]
            idea = GeneratedIdea(
                project_id=project.id,
                topic=topic_name,
                update_copy=copy,
                keywords=json.dumps(['idea', 'test']),
                call_to_action='Call us',
                image_concept='A nice photo',
                ai_provider='gemini',
                fingerprint=compute_idea_fingerprint(topic_name, copy)
            )
            db.session.add(idea)
        db.session.commit()
        
        # Trend Analysis
        for i in range(8):
            trend = TrendAnalysis(
                project_id=project.id,
                topic=topics[i][0],
                occurrence_count=5 + i,
                competitor_count=5,
                total_competitors=5,
                percentage=10.0 + i
            )
            db.session.add(trend)
        db.session.commit()
