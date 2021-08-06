from collections import defaultdict
from tqdm import tqdm
from wordcloud import WordCloud
from pyvis.network import Network
from soynlp.noun import LRNounExtractor_v2
from soynlp.vectorizer import sent_to_word_contexts_matrix
from soynlp.word import pmi
from networkx.readwrite import json_graph
from pprint import pformat
from spacy.lang.en.stop_words import STOP_WORDS

import logging
import kss
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import networkx as nx
import math
import json
import helper
import spacy
import warnings
import sys

sys.tracebacklimit=0
### LOG SETTING
warnings.filterwarnings('ignore')
log = logging.getLogger(__name__)
log.setLevel(logging.DEBUG)
stream_handler = logging.StreamHandler()
log.addHandler(stream_handler)

### GLOBAL VARIABLES
NUM_NODES = 50
NUM_EDGES = 20
NUM_WORDS = 100
WEIGHT_THRESHOLD = 1.5
NLP_EN = spacy.load('en_core_web_sm')
EXCLUDE_LABELS = set(['DATE', 'TIME', 'PERCENT', 'MONEY', 'QUANTITY', 'ORDINAL', 'CARDINAL'])

plt.rcParams['figure.figsize'] = (16, 8)
plt.rcParams['font.family'] = 'NanumSquare'
plt.rc('axes', unicode_minus=False)

class TinyProcesser():
    '''
    Processer model
    '''
    def __init__(self, **kwargs):
        self.dataset = kwargs.get('dataset', dict())
        self.params = kwargs.get('params', dict())
        self.candidates = list()
        self.tf_score = defaultdict(float)
        self.idf_score = defaultdict(float)
        self.tf_idf_score = defaultdict(float)
        self.graph = dict()

    def save(self, filename):
        df = pd.DataFrame(list(self.tf_idf_score.items()), columns = ['word', 'score'])
        df.to_csv(f'output/score/{filename}_score.txt', sep='\t', encoding='utf-8', index=False)
        top_keys = [k for k,_ in sorted(self.tf_idf_score.items(), key=lambda item: -item[1])][:NUM_WORDS]
        wc = WordCloud(
            font_path='C:/Users/komsco/AppData/Local/Microsoft/Windows/Fonts/NanumSquareEB.ttf',
            background_color='white',
            width=600,
            height=400
        ).generate_from_frequencies(dict((key, self.tf_idf_score[key]) for key in top_keys))
        plt.axis('off')
        plt.imshow(wc)
        plt.savefig(f'output/fig/{filename}_fig.png')

        for key, graph in self.graph.items():
            g_json = json_graph.node_link_data(self.graph[key])
            json.dump(g_json, open(f'output/score/{filename}_graph_{key}.json', 'w'), indent=2)
            plt.figure()
            G = nx.Graph()        
            selected_edges = [(u, v, attrs) for u, v, attrs in self.graph[key].edges(data=True) if u in top_keys[:int(NUM_WORDS*0.1)] and attrs['weight'] > WEIGHT_THRESHOLD]
            G.add_edges_from(selected_edges)
            pos = nx.spring_layout(G, k=7*1/np.sqrt(len(G.nodes())))
            nodes = G.nodes()
            node_size = helper.weight_scaler([self.tf_idf_score[node] for node in nodes], 1000, 4000)
            for i, node in enumerate(nodes):
                G.nodes[node]['value'] = node_size[i]
            edges = nx.get_edge_attributes(G, 'weight')
            nx.draw_networkx_nodes(G, pos, nodelist=nodes, node_size=node_size, alpha=0.6)
            nx.draw_networkx_labels(G, pos, labels=dict(zip(nodes, nodes)), font_family='NanumSquare', font_color='black', font_size=12, font_weight='bold')
            nx.draw_networkx_edges(G, pos, edgelist=edges.keys(), alpha=0.3, width=[x/WEIGHT_THRESHOLD for x in list(edges.values())])
            plt.box(False)
            plt.savefig(f'output/fig/{filename}_graph_{key}.png')
            # plt.show()

            pyvis = Network(height=800, width=800)
            pyvis.from_nx(G)
            pyvis.show(f'output/html/{filename}_demo_{key}.html')

    def run(self):
        self.preprocessing()
        self.select_candidates()
        self.filter_candidates()
        self.tfidf()
        self.make_graph()

    def preprocessing(self):
        log.info('Preprocessing...')
        for lang, textlist in list(self.dataset.items()):
            for i in tqdm(range(len(textlist))):
                if lang == 'ko':
                    self.dataset[lang][i] = kss.split_sentences(textlist[i])
                elif lang == 'en':
                    self.dataset[lang][i] = [sent.text for sent in NLP_EN(textlist[i]).sents]
                else:
                    continue
                self.dataset[lang][i] = [helper.remove_special_char(sent) for sent in self.dataset[lang][i]]
        log.info('_________________________________')

    def select_candidates(self):
        log.info('Extracting candidates...')
        nouns = set()
        for key, docs in list(self.dataset.items()):
            if key == 'ko':
                noun_extractor = LRNounExtractor_v2(verbose=False)
                sents = [sent for sublist in docs for sent in sublist]
                nouns = nouns | set(noun_extractor.train_extract(sents))
            elif key == 'en':
                sents = [sent for sublist in docs for sent in sublist]
                for _, sent in enumerate(tqdm(sents)):
                    doc = NLP_EN(sent)
                    nouns = nouns | set([ent.text for ent in doc.ents if ent.label_ not in EXCLUDE_LABELS])
                    nouns = nouns | set([chunk.text for chunk in doc.noun_chunks])
            else:
                continue
        self.candidates = list(nouns)
        log.debug('Extracted candidates')
        log.debug(pformat(self.candidates[:10]))
        log.info('_________________________________')

    def filter_candidates(self):
        log.info('Filtering candidates...')
        filtered_candidates = set()
        with open('stopwords-ko.txt', 'r') as f:
            stopwords = f.readlines()
            stopwords = [word.strip() for word in stopwords]
        for key in self.candidates:
            if helper.is_korean(key):
                if len(key) < 2 or key in stopwords:
                    continue
            if helper.is_english(key):
                if len(key) < 3 or any(len(word) < 2 for word in key.split()):
                    continue
                if key in STOP_WORDS:
                    continue
            if len(key.split()) > 4 or helper.valid_characters(key) <= 0.5:
                continue
            if helper.check_news_stopwords(key) or helper.check_user_stopwords(key):
                continue
            filtered_candidates.add(key)
        self.candidates = list(filtered_candidates)
        log.debug(pformat('The number of filtered candidates: {}'.format(len(self.candidates))))
        log.debug('Filtered candidates')
        log.debug(pformat(self.candidates[:10]))
        log.info('_________________________________')

    def tfidf(self):
        log.info('Ranking candidates...')
        for i, candidate in enumerate(tqdm(self.candidates)):
            idf_score = 0
            for _, docs in self.dataset.items():
                for doc in docs:
                    total_words = sum([len(sent.split()) for sent in doc])
                    cnt = sum([len(sent.split(candidate)) - 1 for sent in doc])
                    if cnt > 0:
                        idf_score += 1
                    self.tf_score[candidate] += cnt / total_words
            self.idf_score[candidate] = idf_score
        num_doc = len(self.dataset['ko']) + len(self.dataset['en'])
        self.idf_score.update([[candidate, math.log(num_doc / (1+score))] for candidate, score in self.idf_score.items()])
        self.tf_idf_score = {key: self.tf_score[key] * self.idf_score[key] for key in self.tf_score.keys()}
        log.debug(pformat(sorted(list(self.tf_idf_score.items()), key=lambda x: -x[1])))
        log.debug('Top ranked keywords and score:')
        log.debug(pformat(sorted(list(self.tf_idf_score.items()), key=lambda x: -x[1])[:20]))
        log.info('_________________________________')

    def pmi(self):
        log.info('Making a co-occurrence matrix...')
        corpus = list()
        idx2vocab = defaultdict(list)
        pmi_dok = defaultdict(list)
        for key, docs in self.dataset.items():
            corpus = [sent for sublist in docs for sent in sublist]
            corpus = [helper.filter_text(sent, self.candidates) for sent in corpus]
            try:
                x, idx2vocab_elem = sent_to_word_contexts_matrix(
                    corpus,
                    windows=5,
                    min_tf=10,
                    dynamic_weight=False,
                    verbose=True
                )
                pmi_dok_elem, px, py = pmi(
                    x,
                    min_pmi=0,
                    alpha=0.0001
                )
                idx2vocab[key] = idx2vocab_elem
                pmi_dok[key] = pmi_dok_elem
            except:
                log.info('_________________________________')
                return idx2vocab, pmi_dok
        log.info('_________________________________')
        return idx2vocab, pmi_dok

    def make_graph(self, num_nodes=NUM_NODES, num_edges=NUM_EDGES):
        idx2vocab, pmi_dok = self.pmi()
        log.info('Making a graph...')
        c = [k for k, _ in sorted(list(self.tf_idf_score.items()), key=lambda x: -x[1])][:num_nodes]
        for key, value in idx2vocab.items():
            self.graph[key] = nx.Graph()
            vocab2idx = {vocab:idx for idx, vocab in enumerate(value)}
            for i in range(len(c)):
                try:
                    query = vocab2idx[c[i]]
                    submatrix = pmi_dok[key][query,:].tocsr()
                    contexts = submatrix.nonzero()[1]
                    pmi_i = submatrix.data
                
                    most_relateds = [(idx, pmi_ij) for idx, pmi_ij in zip(contexts, pmi_i)]
                    most_relateds = sorted(most_relateds, key=lambda x: -x[1])
                    most_relateds = [(idx2vocab[key][idx], pmi_ij) for idx, pmi_ij in most_relateds][:num_edges]
                    for j in range(len(most_relateds)):
                        node, weight = most_relateds[j]
                        if c[i] == node or self.graph[key].has_edge(c[i], node):
                            continue
                        self.graph[key].add_edge(c[i], node, weight=weight)
                except Exception as e:
                    log.exception(e)
                    continue
                sample_node = sorted(list(self.tf_idf_score.items()), key=lambda x: -x[1])[0][0]
            log.debug(self.graph[key].edges(sample_node, data=True))
            log.info('_________________________________')

