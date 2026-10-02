from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import time

options = Options()
options.add_argument('--headless=new')
options.set_capability('goog:loggingPrefs', {'browser': 'ALL'})

driver = webdriver.Chrome(options=options)
try:
    driver.get("http://localhost:5000")
    time.sleep(2)
    
    # Click New Project
    driver.execute_script("document.querySelector('a[data-page=\"projects\"]').click();")
    time.sleep(1)
    driver.execute_script("document.querySelector('button[onclick=\"ProjectsPage.showCreateModal()\"]').click();")
    time.sleep(1)
    
    logs = driver.get_log('browser')
    print("BROWSER LOGS:")
    for log in logs:
        print(f"{log['level']}: {log['message']}")
        
    driver.save_screenshot('debug_modal.png')
    print("Screenshot saved to debug_modal.png")
finally:
    driver.quit()
