import base64, time, logging
from selenium.webdriver.common.by import By

def is_captcha_page(driver) -> bool:
    indicators = ['recaptcha', 'captcha', 'unusual traffic', 'verify you\'re not a robot', 'sorry, we have detected', 'before you continue', 'verify that you\'re human', '/sorry/']
    try:
        page_source = driver.page_source.lower()
        current_url = driver.current_url.lower()
        page_title = driver.title.lower()
        for indicator in indicators:
            if indicator in page_source or indicator in current_url or indicator in page_title:
                return True
        # Check for reCAPTCHA iframe
        iframes = driver.find_elements(By.TAG_NAME, 'iframe')
        for iframe in iframes:
            src = iframe.get_attribute('src') or ''
            if 'recaptcha' in src.lower() or 'captcha' in src.lower():
                return True
    except Exception:
        pass
    return False

def get_captcha_screenshot(driver) -> str:
    try:
        return driver.get_screenshot_as_base64()
    except:
        return ''

def wait_for_captcha_solve(driver, timeout=300) -> bool:
    # Poll every 2 seconds to see if captcha is gone
    start = time.time()
    while time.time() - start < timeout:
        time.sleep(2)
        if not is_captcha_page(driver):
            return True
    return False
