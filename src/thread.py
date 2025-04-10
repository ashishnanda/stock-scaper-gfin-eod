import threading
from bs4 import BeautifulSoup
import requests

def fetch_and_parse(url, results, index):
    response = requests.get(url)
    if response.status_code == 200:
        soup = BeautifulSoup(response.content, 'html.parser')
        results[index] = soup 
    else:
        results[index] = None

def scrape_urls(urls):
    threads = []
    results = [None] * len(urls)

    for i, url in enumerate(urls):
        thread = threading.Thread(target=fetch_and_parse, args=(url, results, i))
        threads.append(thread)
        thread.start()

    for thread in threads:
        thread.join()

    return results

def clean_soup(soup, class_search):
    if soup.find(class_=class_search) is not None:
        return soup.find(class_=class_search).text.strip()[1:].replace(',', '')
    else:
        return None
