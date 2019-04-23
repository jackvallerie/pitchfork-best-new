# scheduler.py

import schedule, time, requests
from lxml import html

def job():
	print(scrape_info())

def scrape_info():
    page = requests.get('https://www.timeanddate.com/worldclock/nigeria/lagos')
    tree = html.fromstring(page.content)
    
    # retrieve text from HTML
    [lagos_time] = tree.xpath('//*[@id="ct"]/text()')
    return lagos_time


schedule.every(3).seconds.do(job)

while True:
	schedule.run_pending()
	time.sleep(1)