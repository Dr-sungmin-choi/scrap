import requests
from requests_html import HTMLSession
import re
import logging

log = logging.getLogger(__name__)
log.setLevel(logging.INFO)
stream_handler = logging.StreamHandler()
log.addHandler(stream_handler)
### helper function

GOOGLE_DOMAIN = (
    'https://www.google.', 
    'https://google.', 
    'https://webcache.googleusercontent.', 
    'http://webcache.googleusercontent.', 
    'https://policies.google.',
    'https://support.google.',
    'https://maps.google.'
)
USER_AGENT = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.95 Safari/537.36'
NEWS_STOPWORDS = ['무단전재', '배포금지', '무단 전재', '배포 금지', '뉴스', 'news', 'url', 'html', 'http', '기자', '저작권자']
USER_STOPWORDS = ['지난', '올해']

def remove_google_domain(raws):
    links = list()
    for url in raws:
        if url.startswith(GOOGLE_DOMAIN):
            continue
        else:
            links.append(url)
    return links

def get_sources(url):
        try:
            session = HTMLSession()
            response = session.get(url, verify=False)
            return response
        except requests.exceptions.RequestException as e:
            log.exception(e)
        except requests.exceptions.ConnectionError as e:
            log.exception(e)

def remove_special_char(text):
    text = re.sub("[\(\[].*?[\)\]]", '', text)
    text = re.sub('[^A-Za-z가-힣0-9\s.,?!]', ' ', text)
    text = re.sub(r"\s+", ' ', text.lower())
    return text.strip()

def check_news_stopwords(text):
    for stopword in NEWS_STOPWORDS:
        if stopword.lower() in text:
            return True
    return False

def check_user_stopwords(text):
    for stopword in USER_STOPWORDS:
        if stopword.lower() in text:
            return True
    return False

def most_frequent(container):
    return max(set(container), key=container.count)
    
def find_raw_text(sentence, words):
    if len(words) == 1:
        return words[0]
    raw_text = words[0]
    tmp = words[0]
    for i in range(1, len(words)):
        tmp += words[i]
        if sentence.find(tmp) == -1:
            raw_text = raw_text + ' ' + words[i]
            tmp = raw_text
        else:
            raw_text = tmp
    return raw_text