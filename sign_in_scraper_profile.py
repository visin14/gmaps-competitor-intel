"""One-time helper: opens the scraper's Chrome profile so YOU can sign in to Google manually.

Run:  python sign_in_scraper_profile.py
Sign in in the window that opens, then come back here and press Enter. The session is saved in
SCRAPER_PROFILE_DIR (from .env) and reused by every later scrape. Credentials are typed by you
directly into Google; this script never sees them.
"""
import os
from dotenv import load_dotenv

load_dotenv('.env')
os.environ.setdefault('SCRAPER_PROFILE_DIR', 'instance/chrome_profile')

from scraper.gmaps_scraper import get_chrome_driver

driver = get_chrome_driver(headless=False)
driver.get('https://accounts.google.com/')
input('Sign in to Google in the Chrome window, then press Enter here to save and close... ')
driver.quit()
print('Done. Profile saved to', os.environ['SCRAPER_PROFILE_DIR'])
