import pandas as pd
import time
from datetime import date, datetime
import platform
import os.path as osp
from tqdm import tqdm
from collections import defaultdict
import helper
import logging
import logging.handlers
from news import News
from nlp import TinyProcesser
import pytz

URL_FORMAT = 'https://www.google.com/search?q={}&hl=en&tbm=nws&tbs=cdr:1,cd_min:{},cd_max:{}'
NUM_PROCESSOR = 4
UTC = pytz.UTC

log = logging.getLogger(__name__)
log.setLevel(logging.DEBUG)
stream_handler = logging.StreamHandler()
log.addHandler(stream_handler)

class SimpleWorker:
    def __init__(self, **kwargs):
        self.params = kwargs
        self.keyword = kwargs.get('keyword', None)
        self.start_date = datetime.strptime(kwargs.get('start_date'), '%Y%m%d').date()
        self.end_date = datetime.strptime(kwargs.get('end_date'), '%Y%m%d').date()
        self.limit = kwargs.get('limit')
        self.input_path = kwargs.get('input_path', None)
        # self.output_path = osp.abspath(kwargs.get('output_path'))
        self.mode = kwargs.get('mode', 'total')
    
    def summarize(self):
        log.info('_________________________________')
        log.info('Current Worker Description')
        log.info('Working Range:\t{}'.format(self.mode))
        if self.mode == 'process':
            log.info('Input File Path:\t{}'.format(self.input_path))
        else:
            log.info('Target Keywords:\t{}'.format(self.keyword))
            log.info('Query Date Range:\t{} ~ {}'.format(self.start_date, self.end_date))
            log.info('Query Page Limit:\t{}'.format(self.limit))
        # log.info('Total Parameters:\t{}'.format(self.params))
        if platform.system() == 'Windows':
            log.info('Detected OS: \tWindows')
        elif platform.system() == 'Linux':
            log.info('Detected OS: \tMac')
        elif platform.system() == 'Darwin':
            log.info('Detected OS: \tMac')
        else:
            raise OSError('Unknown OS Type')
        log.info('_________________________________')

    def make_urls(self):
        links = list()
        _start_date = self.start_date.strftime('%#m/%#d/%Y')
        _end_date = self.end_date.strftime('%#m/%#d/%Y')
        base_url = URL_FORMAT.format(self.keyword, _start_date, _end_date)
        for i in range(0,self.limit,10):    
            links.append(base_url + '&start={}'.format(i))
        return links

    def prepare(self):
        log.info('Preparing data...')
        if self.mode == 'process':
            self.loader = Loader(input_file=self.params.get('input_path', None))
            return self.loader.load()
        elif self.mode == 'scrap' or self.mode == 'total':
            links = self.make_urls()
            self.scraper = Scraper(keyword=self.keyword, targets=links, params=self.params)
            return self.scraper.run()
        else:
            raise ValueError(f'Invalid mode: {self.mode}')

    def save(self):
        if self.mode == 'scrap':
            self.scraper.save()
        elif self.mode == 'process':
            head, tail = osp.split(self.input_path)
            filename, ext = osp.splitext(tail)
            self.processer.save(filename)
        else:
            filename = self.scraper.save()
            self.processer.save(filename)

    def run(self):
        self.summarize()
        start_time = datetime.now()
        self.targets = self.prepare()
        if self.mode != 'scrap':
            log.info('Processing data...')
            text_list = list()
            for idx in tqdm(range(len(self.targets))):
                if self.targets[idx].status == False or len(self.targets[idx].text) == 0:
                    continue
                text_list.append(self.targets[idx].text)
            self.params['keyword'] = self.targets[0].query
            self.processer = TinyProcesser(dataset=text_list, size=len(text_list), params=self.params)
            output = self.processer.run()
        self.save()
        end_time = datetime.now()
        log.info('Finish.')
        log.info(f'Start Time: \t{start_time}')
        log.info(f'Finish Time: \t{end_time}')
        log.info(f'Run Time: \t{end_time - start_time}')
        log.info('_________________________________')

class Loader:
    def __init__(self, input_file):
        self.input_file = osp.abspath(input_file)
    
    def load(self):
        if self.input_file is None or not osp.exists(self.input_file):
            raise FileNotFoundError("Input file should be placed at {}".format(self.input_file))
        else:
            _, ext = osp.splitext(self.input_file)
            df = pd.DataFrame()
            if ext == '.csv':
                df = pd.read_csv(self.input_file, encoding='utf-8', index_col='id', error_bad_lines=False)
                # log.info(f'fname: {fname}')
                # log.info(f'ext: {ext}')
            elif ext == 'txt':
                df = pd.read_csv(self.input_file, encoding='utf-8', sep='\t', index_col='id', error_bad_lines=False)
            elif ext == '.json':
                df = pd.read_json(self.input_file, orient='records', encoding='utf-8', date_unit='ms')
            df['pub_date'] = pd.to_datetime(df['pub_date'], utc=True)
            output = [News(**kwargs) for kwargs in df.to_dict(orient='records')]
            return output

class Scraper:
    def __init__(self, **kwargs):
        self.keyword = kwargs.get('keyword', '')
        self.targets = kwargs.get('targets', list())
        self.params = kwargs.get('params', defaultdict())
        self.outputs = list()

    def load(self):
        links = list()
        for url in tqdm(self.targets):
            response = helper.get_sources(url)
            child = list(response.html.absolute_links)
            child = helper.remove_google_domain(child)
            if len(child) == 0:
                break
            else:
                links += child
        links = helper.remove_google_domain(links)
        self.outputs = [News(url=link, query=self.keyword) for link in links]

    def call(self):
        # process_map(News.parse, self.outputs, max_workers=NUM_PROCESSOR)
        for i in tqdm(range(len(self.outputs))):
            self.outputs[i].parse()

    def save(self):
        # output_path = self.params['output_path']
        # directory = osp.dirname(output_path)
        # if not osp.exists(directory):
        #     os.makedirs(directory, exist_ok=True)
        query = [article.query for article in self.outputs]
        langs = [article.lang for article in self.outputs]
        titles = [article.title for article in self.outputs]
        dates = [article.pub_date for article in self.outputs]
        text = [article.text for article in self.outputs]
        urls = [article.url for article in self.outputs]
        id = range(len(self.outputs))
        df = pd.DataFrame({
            'id': id,
            'query': query,
            'title': titles,
            'lang': langs,
            'pub_date': dates,
            'text': text,
            'url': urls
        })
        df['pub_date'] = pd.to_datetime(df['pub_date'], utc=True)
        min_date = df['pub_date'].min().strftime('%Y%m%d')
        df.to_csv(f'output/csv/output_{query[0]}_{min_date}.csv', encoding='utf-8')
        df.to_csv(f'output/txt/output_{query[0]}_{min_date}.txt', encoding='utf-8', sep='\t')
        with open(f'output/json/output_{query[0]}_{min_date}.json', 'w', encoding='utf-8') as f:
            df.to_json(f, force_ascii=False, orient='records')
        return 'output_{}_{}'.format(query[0], min_date)

    def run(self):
        log.info('_________________________________')
        log.info('Loading Scraper...')
        self.load()
        log.info(f'The number of collected articles: {len(self.outputs)}')
        log.info('_________________________________')
        log.info('Parsing articles...')
        self.call()
        log.info(f'\nThe number of parsed articles: {len([article for article in self.outputs if article.status])}')
        return self.outputs