import os, time, json, random, logging
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from sqlalchemy.exc import IntegrityError
from scraper.captcha_handler import is_captcha_page
from scraper.media_downloader import download_image
from scraper.parser import parse_updates_html
from utils.fingerprint import compute_fingerprint
from utils.text_utils import detect_topic, detect_keywords

CAPTCHA_WAIT_SECONDS = int(os.environ.get('CAPTCHA_WAIT_SECONDS', 300))
MAX_SCROLLS = int(os.environ.get('SCRAPER_MAX_SCROLLS', 8))
MAX_IMAGES_PER_POST = 4

_LOWER = "translate({0},'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz')"
UPDATES_TAB_XPATHS = [
    f"//*[(self::button or self::a) and @role='tab' and contains({_LOWER.format('@aria-label')},'updates')]",
    f"//*[(self::button or self::a) and @role='tab' and contains({_LOWER.format('.')},'updates')]",
    f"//button[contains({_LOWER.format('@aria-label')},'updates')]",
]
CONSENT_XPATHS = [
    "//button[.//span[contains(., 'Reject all')]]",
    "//button[contains(., 'Reject all')]",
    "//button[.//span[contains(., 'Accept all')]]",
]

FIND_SCROLLER_JS = """
const els = [...document.querySelectorAll('div')].filter(e =>
  e.scrollHeight > e.clientHeight + 50 && e.clientHeight > 200 && getComputedStyle(e).overflowY !== 'visible');
els.sort((a, b) => b.scrollHeight - a.scrollHeight);
return els[0] || null;
"""


# ----------------------------------------------------------------------------- browser

def get_chrome_driver(headless: bool = None):
    """Start Chrome. SCRAPER_HEADLESS=true runs without a window (note: CAPTCHAs then cannot be solved by hand)."""
    if headless is None:
        headless = os.environ.get('SCRAPER_HEADLESS', 'false').lower() == 'true'
    options = Options()
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--window-size=1400,1000')
    options.add_argument('--lang=en-US')
    options.add_argument('--disable-blink-features=AutomationControlled')
    options.add_experimental_option('excludeSwitches', ['enable-automation'])
    if os.environ.get('CHROME_BINARY'):
        options.binary_location = os.environ['CHROME_BINARY']
    # Optional dedicated profile: sign in to Google once in this window and the session is reused on later
    # scrapes (can expose tabs hidden when signed out and reduces CAPTCHAs). Use a folder only the scraper uses.
    if os.environ.get('SCRAPER_PROFILE_DIR'):
        options.add_argument(f'--user-data-dir={os.path.abspath(os.environ["SCRAPER_PROFILE_DIR"])}')
    if headless:
        options.add_argument('--headless=new')

    try:
        from webdriver_manager.chrome import ChromeDriverManager
        service = Service(ChromeDriverManager().install())
    except Exception:
        service = Service()  # fall back to Selenium Manager / chromedriver on PATH

    driver = webdriver.Chrome(service=service, options=options)
    driver.set_page_load_timeout(45)
    return driver


def _click_first(driver, xpaths, timeout=6) -> bool:
    for xp in xpaths:
        try:
            el = WebDriverWait(driver, timeout).until(lambda d, xp=xp: d.find_element(By.XPATH, xp))
            driver.execute_script('arguments[0].click();', el)
            return True
        except Exception:
            continue
    return False


def _handle_consent(driver):
    if 'consent.google' in driver.current_url.lower():
        _click_first(driver, CONSENT_XPATHS, timeout=4)
        time.sleep(2)


def _scroll_updates(driver):
    """Scroll the side panel until no more content loads."""
    last_height = -1
    for _ in range(MAX_SCROLLS):
        height = driver.execute_script(
            FIND_SCROLLER_JS.replace('return els[0] || null;',
                                     'const s = els[0]; if (!s) return -1; s.scrollTop = s.scrollHeight; return s.scrollHeight;'))
        if height in (-1, last_height):
            break
        last_height = height
        time.sleep(1.5)


def _save_debug_snapshot(driver, app_root, competitor, reason):
    try:
        folder = os.path.join(app_root, 'instance', 'scrape_debug')
        os.makedirs(folder, exist_ok=True)
        stamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
        base = os.path.join(folder, f'{competitor.id}_{stamp}')
        with open(base + '.html', 'w', encoding='utf-8') as f:
            f.write(driver.page_source)
        driver.save_screenshot(base + '.png')
        return f'{reason} (debug snapshot: instance/scrape_debug/{os.path.basename(base)}.html)'
    except Exception:
        return reason


# ----------------------------------------------------------------------------- CAPTCHA

def _await_manual_verification(driver, job, log, pause_event, db) -> bool:
    """Pause for a human. Returns True once the verification is gone (solved in the browser or Resume clicked)."""
    log.captcha_encountered = True
    log.manual_intervention = True
    job.captcha_required = True            # permanent record that manual intervention was needed
    job.status = 'awaiting_verification'   # drives the UI alert
    db.session.commit()

    pause_event.clear()
    deadline = time.time() + CAPTCHA_WAIT_SECONDS
    solved = False
    while time.time() < deadline:
        if pause_event.wait(timeout=2) or not is_captcha_page(driver):
            time.sleep(2)
            solved = not is_captcha_page(driver)
            if solved:
                break
            pause_event.clear()  # Resume clicked but still blocked: keep waiting
    pause_event.clear()
    job.status = 'running'
    db.session.commit()
    return solved


# ----------------------------------------------------------------------------- scraping

def scrape_competitor(driver, competitor, log, job, pause_event, app):
    """Scrape one competitor into the repository. Fills `log`; never raises."""
    from models import db, Post

    found = new = dup = images_downloaded = 0
    log.status = 'running'
    db.session.commit()
    try:
        driver.get(competitor.gmaps_url)
        _handle_consent(driver)
        WebDriverWait(driver, 20).until(lambda d: d.execute_script('return document.readyState') == 'complete')
        time.sleep(3)

        if is_captcha_page(driver) and not _await_manual_verification(driver, job, log, pause_event, db):
            log.status = 'failed'
            log.error_info = 'CAPTCHA/verification was not completed in time'
            return

        if not _click_first(driver, UPDATES_TAB_XPATHS):
            log.status = 'no_updates'
            log.error_info = _save_debug_snapshot(driver, app.root_path, competitor,
                                                  'No "Updates" tab found on this profile (it may not publish updates)')
            return
        time.sleep(2)

        if is_captcha_page(driver) and not _await_manual_verification(driver, job, log, pause_event, db):
            log.status = 'failed'
            log.error_info = 'CAPTCHA/verification was not completed in time'
            return

        _scroll_updates(driver)
        scraped = parse_updates_html(driver.page_source)
        if not scraped:
            log.status = 'no_updates'
            log.error_info = _save_debug_snapshot(driver, app.root_path, competitor, 'Updates tab opened but no posts were recognised')
            return

        media_root = os.path.join(app.root_path, app.config['MEDIA_FOLDER'])
        web_prefix = app.config['MEDIA_FOLDER'].replace('\\', '/')
        seen = set()
        for pdata in scraped:
            found += 1
            fp = compute_fingerprint(post_url=pdata['url'], post_text=pdata['text'],
                                     competitor_id=competitor.id, project_id=competitor.project_id)
            if fp in seen or Post.query.filter_by(fingerprint=fp).first():
                dup += 1
                continue
            seen.add(fp)

            local_images = []
            for i, src in enumerate(pdata['images'][:MAX_IMAGES_PER_POST]):
                path = download_image(src, competitor.project_id, competitor.id, f'p{fp[:6]}_{i}', media_root, web_prefix)
                if path:
                    local_images.append(path)
            images_downloaded += len(local_images)

            db.session.add(Post(
                project_id=competitor.project_id, competitor_id=competitor.id, competitor_name=competitor.name,
                post_url=pdata['url'], post_text=pdata['text'], published_date=pdata['date'],
                images=json.dumps(local_images), call_to_action=pdata['cta'],
                detected_keywords=json.dumps(detect_keywords(pdata['text'])), detected_topic=detect_topic(pdata['text']),
                source_url=competitor.gmaps_url, fingerprint=fp, scrape_job_id=job.id))
            try:
                db.session.commit()
                new += 1
            except IntegrityError:
                db.session.rollback()
                dup += 1
        log.status = 'success'
    except Exception as e:
        db.session.rollback()
        log.status = 'failed'
        log.error_info = f'{type(e).__name__}: {str(e)[:400]}'
        logging.exception('Scrape failed for %s', competitor.name)
    finally:
        log.posts_found, log.new_posts, log.duplicates_skipped, log.images_downloaded = found, new, dup, images_downloaded
        log.end_time = datetime.utcnow()
        db.session.commit()


def run_scrape_job(app, job_id, competitor_ids, pause_event):
    """Process competitors one by one, recording a ScrapeLog for each."""
    from models import db, ScrapeJob, ScrapeLog, Competitor, Post

    with app.app_context():
        job = db.session.get(ScrapeJob, job_id)
        if not job:
            return

        driver, outcomes = None, []
        try:
            try:
                driver = get_chrome_driver()
                startup_error = None
            except Exception as e:
                startup_error = f'Could not start Chrome: {type(e).__name__}: {str(e)[:300]}'

            for competitor_id in competitor_ids:
                competitor = db.session.get(Competitor, competitor_id)
                if not competitor or competitor.project_id != job.project_id:
                    job.processed_competitors += 1
                    db.session.commit()
                    continue

                log = ScrapeLog(job_id=job.id, competitor_id=competitor.id, competitor_name=competitor.name, status='pending')
                db.session.add(log)
                competitor.scrape_status = 'running'
                db.session.commit()

                if startup_error:
                    log.status, log.error_info, log.end_time = 'failed', startup_error, datetime.utcnow()
                else:
                    scrape_competitor(driver, competitor, log, job, pause_event, app)

                competitor.scrape_status = {'failed': 'failed', 'no_updates': 'no_updates'}.get(log.status, 'done')
                competitor.last_scraped_at = datetime.utcnow()
                competitor.total_posts = Post.query.filter_by(competitor_id=competitor.id).count()
                job.processed_competitors += 1
                db.session.commit()
                outcomes.append(log.status)

                if driver and competitor_id != competitor_ids[-1]:
                    time.sleep(random.uniform(3, 6))  # be polite between profiles
        except Exception as e:
            db.session.rollback()
            logging.exception('Scrape job %s crashed', job_id)
            outcomes.append('failed')
        finally:
            if driver:
                try:
                    driver.quit()
                except Exception:
                    pass
            job = db.session.get(ScrapeJob, job_id)
            failed = sum(1 for o in outcomes if o == 'failed')
            job.status = 'failed' if outcomes and failed == len(outcomes) or not outcomes else ('partial' if failed else 'done')
            job.ended_at = datetime.utcnow()
            db.session.commit()
