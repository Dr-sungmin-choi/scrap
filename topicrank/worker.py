import multiprocessing
import pandas as pd
import time
from datetime import date, datetime
import platform
import os.path as osp
from tqdm import tqdm
from tqdm.contrib.concurrent import process_map
from multiprocessing import Pool, Array
import helper
import logging
import logging.handlers
from news import News
from nlp import BigProcesser, UnitProcesser

URL_FORMAT = 'https://www.google.com/search?q={}&hl=en&tbm=nws&tbs=cdr:1,cd_min:{},cd_max:{}'
NUM_PROCESSOR = 4

log = logging.getLogger(__name__)
log.setLevel(logging.INFO)
stream_handler = logging.StreamHandler()
log.addHandler(stream_handler)

class Worker:
    def __init__(self, **kwargs):
        self.params = kwargs
        self.keyword = kwargs.get('keyword', None)
        self.start_date = datetime.strptime(kwargs.get('start_date'), '%Y%m%d').date()
        self.end_date = datetime.strptime(kwargs.get('end_date'), '%Y%m%d').date()
        self.limit = kwargs.get('limit')
        self.input_path = kwargs.get('input_path', None)
        # self.output_path = osp.abspath(kwargs.get('output_path'))
        self.mode = kwargs.get('mode', 'total')
        self.executable = ''
        if platform.system() == 'Windows':
            self.executable = './chromedriver/chromedriver_win.exe'
        elif platform.system() == 'Linux':
            self.executable = './chromedriver/chromedriver_linux'
        elif platform.system() == 'Darwin':
            self.executable = './chromedriver/chromedriver_mac'
        else:
            raise OSError('Unknown OS Type')
        if not osp.exists(self.executable):
            raise FileNotFoundError('Chromedriver file should be placed at {}'.format(self.executable))
        
    def summarize(self):

        log.info('_________________________________')
        log.info('Current Worker Description')
        log.info('Worker Mode:\t{}'.format(self.mode))
        if self.mode == 'process':
            log.info('Input File Path:\t{}'.format(self.input_path))
        else:
            log.info('Target Keywords:\t{}'.format(self.keyword))
            log.info('Query Date Range:\t{} ~ {}'.format(self.start_date, self.end_date))
            log.info('Query Page Limit:\t{}'.format(self.limit))
        # log.info('Output File Path:\t{}'.format(self.output_path))
        log.info('Total Parameters:\t{}'.format(self.params))
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
            self.targets = self.loader.load()
        elif self.mode == 'scrap' or self.mode == 'total':
            links = self.make_urls()
            self.scraper = Scraper(keyword=self.keyword, targets=links, params=self.params)
            self.scraper.run()
        else:
            raise ValueError(f'Invalid mode: {self.mode}')
        log.info('_________________________________')

    def run(self, cycle=True):
        self.summarize()
        start_time = datetime.now()
        self.prepare()
        log.info('Processing data...')
        if self.mode != 'scrap':
            # For BigProcesser
            if cycle:
                self.processer = BigProcesser()
                for idx in tqdm(range(len(self.targets))):
                    if self.targets[idx].status == False or len(self.targets[idx].text) == 0:
                        continue
                    element = UnitProcesser(text=self.targets[idx].text, lang=self.targets[idx].lang, cycle=cycle)
                    element.run()
                    self.processer.processers.append(element)
                self.processer.run()

            # For UnitProcesser (unit test)
            else:
                idx = 0
                if len(self.targets[idx].text) > 0:
                    element = UnitProcesser(text=self.targets[idx].text, lang=self.targets[idx].lang, cycle=cycle)
                    element.run()
        log.info('_________________________________')
        end_time = datetime.now()
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
            elif ext == '.json':
                df = pd.read_json(self.input_file, orient='records', encoding='utf-8', date_unit='ms')
            df['pub_date'] = pd.to_datetime(df['pub_date'], unit='ms')
            output = [News(**kwargs) for kwargs in df.to_dict(orient='records')]
            return output

class Scraper:
    def __init__(self, keyword, targets, params):
        self.keyword = keyword
        self.targets = targets
        self.params = params
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
        for article in tqdm(self.outputs):
            article.parse()

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
        df.to_csv(f'output/output_{query[0]}.csv', encoding='utf-8')
        with open(f'output/output_{query[0]}.json', 'w', encoding='utf-8') as f:
            df.to_json(f, force_ascii=False, orient='records')
        
    def run(self):
        log.info('_________________________________')
        log.info('Loading Scraper...')
        self.load()
        log.info(f'The number of collected articles: {len(self.outputs)}')
        log.info('_________________________________')
        log.info('Parsing articles...')
        self.call()
        log.info(f'\nThe number of parsed articles: {len([article for article in self.outputs if article.status])}')
        log.info('_________________________________')
        log.info('Saving outputs...')
        # log.info('Saving outputs in the file: "{}"...'.format(self.params['output_path']))
        self.save()