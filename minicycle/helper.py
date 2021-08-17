from requests_html import HTMLSession
import re
import logging

### LOG SETTING
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)
stream_handler = logging.StreamHandler()
log.addHandler(stream_handler)

### GLOBAL VARIABLES
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
NEWS_STOPWORDS = ['news', '무단전재', '배포금지', '무단 전재', '배포 금지', '기사']
USER_STOPWORDS = ['javascript', '이메일', 'commas', 'type address', 'your email', 'image','페이스북', '카카오톡', '인스타그램', '트위터', 'sns', '공유']

def remove_google_domain(raws):
    '''
    Remove google domain urls to detect no search result
    '''
    links = list()
    for url in raws:
        if url.startswith(GOOGLE_DOMAIN):
            continue
        else:
            links.append(url)
    return links

def get_sources(url):
    '''
    Make HTML requests
    '''
    try:
        session = HTMLSession()
        response = session.get(url, verify=False)
        return response
    except Exception as e:
        log.exception(e)

def remove_special_char(text):
    '''
    Preprocess text
    '''
    text = re.sub("\S+@\S+", " ", text)
    text = re.sub("http\S+", " ", text)
    text = re.sub("[\(\[].*?[\)\]]", "", text)
    text = re.sub("[^A-Za-z가-힣0-9'`]", " ", text)
    text = re.sub(r"\s+", " ", text.lower())
    return text.strip()

def valid_characters(text):
    valid_characters = re.sub("[^A-Za-z가-힣0-9]", "", text.lower())
    return len(valid_characters) / float(len(text))

def filter_text(text, candidates):
    '''
    Make text only containing candidates
    '''
    output = list()
    tokens = text.split()
    for i, token in enumerate(tokens):
        for candidate in candidates:
            if candidate in tokens[i]:
                output.append(candidate)
    return ' '.join(output)

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

def is_korean(text):
    text = ''.join(text.split())
    def is_korean_character(char):
        value = ord(char)
        return value >=4352 and value <= 4607
    return all(is_korean_character(i) for i in text)

def is_english(text):
    text = ''.join(text.split())
    return text.isalnum()

def weight_scaler(weights, min_value, max_value):
    '''
    Rescale
    '''
    try:
        min_weight = min(weights)
        max_weight = max(weights)
        weights_scaled = [(x - min_weight) / (max_weight - min_weight) for x in weights]
        weights_scaled = [x * (max_value - min_value) + min_value for x in weights_scaled]
        return weights_scaled
    except:
        return weights