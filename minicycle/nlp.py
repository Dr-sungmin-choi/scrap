import logging
from nltk import RegexpParser
from collections import defaultdict
from wordcloud import WordCloud
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import networkx as nx
import kss
from kiwipiepy import Kiwi
from soynlp.noun import LRNounExtractor_v2
from soynlp.vectorizer import sent_to_word_contexts_matrix
from soynlp.word import pmi
from networkx.readwrite import json_graph
from pprint import pformat
import math
import json
import helper
import warnings

warnings.filterwarnings('ignore')
log = logging.getLogger(__name__)
log.setLevel(logging.DEBUG)
stream_handler = logging.StreamHandler()
log.addHandler(stream_handler)

MIN_TOKEN = 1
MAX_TOKEN = 3
GRAMMAR = r'''
            NP: {<Noun|Alpha|Number|Suffix>*}
                # {<NNG|NNP|NR|NP|SL>*<NNB>?}
                {<NNG|NNP|NR|NP|SL>+<NNG|NNP|NR|NP|SL|SN>*}
            VP: {<V.*>*}
            AP: {<A.*>*}
        '''
CHUNKER = RegexpParser(GRAMMAR)
NUM_NODES = 50
NUM_EDGES = 20
NUM_WORDS = 50
WEIGHT_THRESHOLD = 2.2

plt.rcParams['figure.figsize'] = (16, 8)
plt.rcParams['font.family'] = 'NanumSquare'
plt.rc('axes', unicode_minus=False)

kiwi = Kiwi()
kiwi.prepare()

class Sentence():
    def __init__(self, **kwargs):
        self.sent = kwargs.get('sent', '')
        self.words = kwargs.get('words', list())
        self.pos = kwargs.get('pos', list())
        self.length = len(self.words)

    def __repr__(self):
        return self.sent

class Candidate():
    def __init__(self, **kwargs):
        self.offsets = kwargs.get('offsets', list())
        self.raw_form = kwargs.get('raw_form', list())
        self.pos_pattern = kwargs.get('pos_pattern', list())
        self.sent_id = kwargs.get('sent_id', list())

    def __repr__(self):
        return str(list(zip(self.raw_form, self.offsets, self.sent_id)))

class TinyProcesser():
    
    def __init__(self, **kwargs):
        self.dataset = kwargs.get('dataset', list())
        self.size = kwargs.get('size', 0)
        self.params = kwargs.get('params', defaultdict())
        self.candidates = defaultdict()
        self.tf_score = defaultdict()
        self.idf_score = defaultdict()
        self.tf_idf_score = defaultdict()
        self.graph = nx.Graph()

    def run(self):
        self.preprocessing()
        self.select_candidates()
        self.filter_candidates()
        self.simpleTfIdf()
        idx2vocab, pmi_dok = self.pmi()
        self.make_graph(idx2vocab, pmi_dok)
        return self.tf_idf_score

    def preprocessing(self):
        for i, _ in enumerate(self.dataset):
            self.dataset[i] = self.dataset[i].replace(',', ' ')
            self.dataset[i] = helper.remove_special_char(self.dataset[i])
    
    def save(self, filename):
        df = pd.DataFrame(list(self.tf_idf_score.items()), columns = ['word', 'score'])
        df.to_csv(f'output/score/{filename}_score.txt', sep='\t', encoding='utf-8', index=False)
        top_keys = [k for k,v in sorted(self.tf_idf_score.items(), key=lambda item: -item[1])][:NUM_WORDS]
        wc = WordCloud(
            font_path='C:/Users/komsco/AppData/Local/Microsoft/Windows/Fonts/NanumSquareEB.ttf',
            background_color='white',
            width=600,
            height=400
        ).generate_from_frequencies(dict((key, self.tf_idf_score[key]) for key in top_keys))
        plt.imshow(wc)
        plt.axis('off')
        plt.savefig(f'output/fig/{filename}_fig.png')
        # plt.show()
        plt.figure()
        g_json = json_graph.node_link_data(self.graph)
        json.dump(g_json, open(f'output/score/{filename}_graph.json', 'w'), indent=2)

        keys = list(nx.get_edge_attributes(self.graph, 'weight').keys())
        weights = list(nx.get_edge_attributes(self.graph, 'weight').values())
        scaled_weights = helper.weight_scaler(weights, 1, 100)

        G = nx.Graph()        
        for pair, weight in zip(keys, scaled_weights):
            if not G.has_edge(pair[0], pair[1]):
                G.add_edge(pair[0], pair[1], weight=weight)
        # selected_edges = [(u, v, attrs) for u, v, attrs in G.edges(data=True) if attrs['weight'] > WEIGHT_THRESHOLD]
        # selected_edges = [(u, v, attrs) for u, v, attrs in self.graph.edges(data=True) if attrs['weight'] > WEIGHT_THRESHOLD]
        selected_edges = [(u, v, attrs) for u, v, attrs in self.graph.edges(data=True) if u in top_keys[:int(NUM_WORDS/10)] and attrs['weight'] > WEIGHT_THRESHOLD]
        H = nx.Graph()
        H.add_edges_from(selected_edges)
        for _, _, d in H.edges(data=True):
            d['weight'] = round(d['weight'], 3)
        pos = nx.spring_layout(H, k=7*1/np.sqrt(len(H.nodes())))
        nodes = H.nodes()
        node_size = helper.weight_scaler([self.tf_idf_score[node] for node in nodes], 1000, 4000)
        edges = nx.get_edge_attributes(H, 'weight')
        nx.draw_networkx_nodes(H, pos, nodelist=nodes, node_size=node_size, alpha=0.6)
        nx.draw_networkx_labels(H, pos, labels=dict(zip(nodes, nodes)), font_family='NanumSquare', font_color='black', font_size=12, font_weight='bold')
        nx.draw_networkx_edges(H, pos, edgelist=edges.keys(), alpha=0.3, width=[x/WEIGHT_THRESHOLD for x in list(edges.values())])
        plt.box(False)
        plt.savefig(f'output/fig/{filename}_graph.png')
        # plt.show()

    def select_candidates(self):
        log.info('Extracting candidates...')
        noun_extractor = LRNounExtractor_v2(verbose=True)
        nouns = noun_extractor.train_extract(self.dataset)
        self.candidates = nouns
        log.info('Extracted candidates')
        log.info(pformat(sorted(list(self.candidates.items()), key=lambda x: -x[1].frequency)[5:10]))
        log.info(pformat(list(noun_extractor._compounds_components.items())[2:7]))
        log.info('_________________________________')

    def simpleTfIdf(self):
        log.info('Ranking candidates...')
        c = list(self.candidates.keys())
        f_dataset = list()
        for i, _ in enumerate(self.dataset):
            f_dataset.append(helper.filter_text(self.dataset[i], c))
        total_words = sum([len(text.split()) for text in f_dataset])
        total_num_text = len(f_dataset)
        for each_c in c:
            for i, _ in enumerate(self.dataset):
                cnt = len(self.dataset[i].split(each_c)) - 1
                num_words = len(self.dataset[i].split()) - 1
                self.tf_score[each_c] = self.tf_score.get(each_c, 0) + cnt / num_words
            self.idf_score[each_c] = sum([ 1 if each_c in dataset else 0 for dataset in f_dataset])
        self.tf_score.update([[candidate, tf/total_words] for candidate, tf in self.tf_score.items()])
        self.idf_score.update([[candidate, math.log(total_num_text / idf)] for candidate, idf in self.idf_score.items()])
        self.tf_idf_score = {key: self.tf_score[key] * self.idf_score[key] for key in self.tf_score.keys()}
        log.debug('Top ranked keywords and score:')
        log.debug(pformat(sorted(list(self.tf_idf_score.items()), key=lambda x: -x[1])[:20]))
        log.info('_________________________________')

    def pmi(self):
        log.info('Making a co-occurrence matrix...')
        corpus = list()
        c = list(self.candidates.keys())
        for doc in self.dataset:
            sents = kss.split_sentences(doc)
            for i, _ in enumerate(sents):
                corpus.append(helper.filter_text(sents[i], c))
        x, idx2vocab = sent_to_word_contexts_matrix(
            corpus,
            windows=5,
            min_tf=10,
            dynamic_weight=False,
            verbose=True
        )
        pmi_dok, px, py = pmi(
            x,
            min_pmi=0,
            alpha=0.0001
        )
        log.info('_________________________________')
        return idx2vocab, pmi_dok

    def make_graph(self, idx2vocab, pmi_dok, num_nodes=NUM_NODES, num_edges=NUM_EDGES):
        log.info('Making a graph...')
        c = [k for k, _ in sorted(list(self.tf_idf_score.items()), key=lambda x: -x[1])][:num_nodes]
        vocab2idx = {vocab:idx for idx, vocab in enumerate(idx2vocab)}
        for i in range(len(c)):
            try:
                query = vocab2idx[c[i]]
                submatrix = pmi_dok[query,:].tocsr()
                contexts = submatrix.nonzero()[1]
                pmi_i = submatrix.data
            
                most_relateds = [(idx, pmi_ij) for idx, pmi_ij in zip(contexts, pmi_i)]
                most_relateds = sorted(most_relateds, key=lambda x: -x[1])
                most_relateds = [(idx2vocab[idx], pmi_ij) for idx, pmi_ij in most_relateds][:num_edges]
                for j in range(len(most_relateds)):
                    node, weight = most_relateds[j]
                    if c[i] == node or self.graph.has_edge(c[i], node):
                        continue
                    self.graph.add_edge(c[i], node, weight=weight)
            except Exception as e:
                log.exception(e)
                continue
        sample_node = sorted(list(self.tf_idf_score.items()), key=lambda x: -x[1])[0][0]
        log.debug(self.graph.edges(sample_node, data=True))
        log.info('_________________________________')

    def filter_candidates(self):
        stopwords = list()
        with open('stopwords-ko.txt', 'r') as f:
            stopwords = f.readlines()
            stopwords = [word.strip() for word in stopwords]
        for key in list(self.candidates):
            if len(key) < 2:
                self.candidates.pop(key, None)
            elif helper.valid_characters(key) <= 0.5:
                self.candidates.pop(key, None)
            elif key in stopwords:
                self.candidates.pop(key, None)
            elif helper.check_news_stopwords(key):
                self.candidates.pop(key, None)
            elif helper.check_user_stopwords(key):
                self.candidates.pop(key, None)
            elif key != self.params['keyword'] and (key in self.params['keyword'] or self.params['keyword'] in key):
                self.candidates.pop(key, None)
        log.debug(pformat('The number of keyword candidates: {}'.format(len(self.candidates))))
        log.info('_________________________________')

