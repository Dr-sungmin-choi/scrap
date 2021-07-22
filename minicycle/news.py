from newspaper import Article
from newspaper import Config
from langdetect import detect
from languages_countries import convert
import re
import logging
import warnings

USER_AGENT = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/50.0.2661.102 Safari/537.36'
config = Config()
config.browser_user_agent = USER_AGENT
config.request_timeout=10

warnings.filterwarnings('ignore')
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)
stream_handler = logging.StreamHandler()
log.addHandler(stream_handler)

# title, lang, pubDate, text, url
class News(object):
    def __init__(self, **kwargs):
        self.url = kwargs.get('url', '')
        self.title = kwargs.get('title', '')
        self.text = kwargs.get('text', '')
        self.pub_date = kwargs.get('pub_date', None)
        self.query = kwargs.get('query', '')
        self.lang = kwargs.get('lang', '')
        self.status = True

    def __repr__(self):
        return self.title 

    def parse(self):
        try:
            article = Article(self.url, config=config)
            article.download()
            article.parse()
            self.title = article.title
            self.text = re.sub(r"[\n\t\s]+", ' ', article.text)
            self.pub_date = article.publish_date
            self.lang = detect(self.text) if self.text is not None or len(self.text) > 0 else ''
        except Exception as e:
            self.status = False
            # log.exception(e)

    def summarize(self):
        log.info(f'Article Query:\t{self.query}')
        log.info(f'Article Source:\t{self.url}')
        log.info(f'Article Title:\t{self.title}')
        log.info(f'Article Date:\t{self.pub_date}')
        log.info('Article Lang:\t{}'.format(self.lang + ', ' + convert(self.lang)))
        log.info(f'Article Text:\t{self.text[:100]+"..."}')