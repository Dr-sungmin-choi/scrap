import logging
from nltk import RegexpParser
# import numpy as np
from collections import defaultdict
from PIL import Image
from wordcloud import WordCloud
from statistics import mode
from networkx.readwrite import json_graph
import matplotlib.pyplot as plt
import networkx as nx
# from konlpy.tag import Okt
from kiwipiepy import Kiwi
from sklearn.feature_extraction.text import CountVectorizer
from scipy.cluster.hierarchy import linkage, fcluster, dendrogram
from kss import split_sentences
from languages_countries import convert
from tqdm import tqdm
import json
import helper
import warnings

warnings.filterwarnings('ignore')
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)
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
plt.rcParams['figure.figsize'] = (12, 6)
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

class BigProcesser():
    def __init__(self, **kwargs):
        self.topics = list()
        self.graph = nx.Graph()
        self.processers = list()
        self.candidates = list()

    def run(self):
        log.info('Clustering topics...')
        self.cluster_topic()
        log.info('_________________________________')
        log.info('Making a graph...')
        self.make_graph()
        # show fig or not
        self.show_graph()
        self.topic_ranking()

    def cluster_topic(self, strategy='average', threshold=1.3):
        candidates = [list(processer.graph.nodes) for processer in self.processers]
        candidates = list(set([item for sublist in candidates for item in sublist]))
        count = CountVectorizer()
        X = count.fit_transform(candidates)
        Z = linkage(X.toarray(), strategy)
        clusters = fcluster(Z, t=threshold, criterion='distance')
        for cluster_id in range(1, max(clusters) + 1):
            log.debug(f'cluster {cluster_id}: {[candidates[j] for j in range(len(clusters)) if clusters[j] == cluster_id]}')
            self.topics.append([candidates[j] for j in range(len(clusters)) if clusters[j] == cluster_id])

    # def make_graph(self):
    #     edges = [list(processer.graph.edges(data=True)) for processer in self.processers]
    #     edges = [item for sublist in edges for item in sublist]
    #     edges = [item for item in edges if item[2]['weight'] > 0]
    #     self.graph = nx.Graph()
    #     for u, v, attrs in edges:
    #         if self.graph.has_edge(u, v):
    #             self.graph[u][v]['weight'] += attrs['weight']
    #         else:
    #             self.graph.add_edge(u, v, weight=0.0)
    #     labels = nx.get_edge_attributes(self.graph, 'weight')
    #     self.graph.remove_edges_from((e for e, w in labels.items() if w == 0))
    #     for _, _, d in self.graph.edges(data=True):
    #         d['weight'] = round(d['weight'], 3)
    
    def make_graph(self):
        t = [helper.most_frequent(topic) for topic in self.topics]
        log.debug(t)
        for i in tqdm(range(len(self.topics))):
            for j in range(len(self.topics)):
                self.graph.add_edge(t[i], t[j], weight=0.0)
                for c_i in self.topics[i]:
                    for c_j in self.topics[j]:
                        for p in self.processers:
                            if p.graph.has_edge(c_i, c_j):
                                self.graph[t[i]][t[j]]['weight'] += p.graph[c_i][c_j]['weight']
        log.debug(sorted(list(self.graph.edges(data=True)))[:100])
        g_json = json_graph.node_link_data(self.graph)
        json.dump(g_json, open('graph_json', 'w'), indent=2)


    def show_graph(self, threshold=3):
        selected_edges = [(u, v, attrs) for u, v, attrs in self.graph.edges(data=True) if attrs['weight'] > threshold]
        G = nx.Graph()        
        G.add_edges_from(selected_edges)
        for _, _, d in G.edges(data=True):
            d['weight'] = round(d['weight'], 3)
        pos = nx.spring_layout(G)
        nx.draw_networkx_nodes(G, pos)
        nx.draw_networkx_labels(G, pos, font_family='NanumSquare', font_size=8, font_weight='bold')
        nx.draw_networkx_edges(G, pos)
        # nx.draw_networkx_edge_labels(G, pos, edge_labels=nx.get_edge_attributes(G, 'weight'), font_size=5)
        plt.show()

    def topic_ranking(self, strategy='first'):
        w = nx.pagerank_scipy(self.graph, alpha=0.85, weight='weight')
        log.debug(w)
        wc = WordCloud(
            font_path='C:/Users/komsco/AppData/Local/Microsoft/Windows/Fonts/NanumSquareEB.ttf',
            background_color='white',
            width=600,
            height=400
        ).generate_from_frequencies(w)
        plt.imshow(wc)
        plt.axis('off')
        plt.show()

class UnitProcesser():
    def __init__(self, **kwargs):
        self.lang = kwargs.get('lang', 'en')
        self.text = kwargs.get('text', '')
        self.sentences = list()
        self.candidates = defaultdict(Candidate)
        self.topics = list()
        self.graph = nx.Graph()
        self.cycle = kwargs.get('cycle', True)
    
    def run(self):
        self.select_candidates()
        self.filter_candidates()
        if self.cycle:
            self.make_raw_graph()
            
        else:
            self.cluster_topic()
            self.make_raw_graph()
        if not self.cycle:
            self.show_graph()
            self.topic_ranking()

    def select_candidates(self):
        text = helper.remove_special_char(self.text)
        if self.lang == 'ko':
            sentTokens = split_sentences(text)
            # okt = Okt()
            for i, sent in enumerate(sentTokens):
                shift = sum([len(s) for s in sentTokens[:i]])
                tokens = kiwi.analyze(sent, 1)[0][0]
                words = [token[0] for token in tokens]
                pos = [token[1] for token in tokens]
                starts = [token[2] + shift for token in tokens]
                sentObject = Sentence(sent=sent, words=words, pos=pos)
                self.sentences.append(sentObject)

                tuples = [(str(j), pos[j]) for j in range(len(pos))]
                tree = CHUNKER.parse(tuples)
                log.debug(f'{i}th sentence: {sent}')
                log.debug(f'{i}th tagger: {tokens}')
                for subtree in tree.subtrees():
                    if subtree.label() == 'NP':
                        leaves = subtree.leaves()
                        first = int(leaves[0][0])
                        last = int(leaves[-1][0])
                        self.add_candidate(
                            words=words[first:last + 1],
                            pos=pos[first:last + 1],
                            offset=starts[first],
                            sentence_id=i
                        )
        elif self.lang == 'en':
            ### TODO ###
            self.sentences = list()
        else:
            log.warning('No tokenizer for {}'.format(convert(self.lang)))

    def add_candidate(self, words, pos, offset, sentence_id):
        key = helper.find_raw_text(self.sentences[sentence_id].sent, words)
        self.candidates[key].offsets.append(offset)
        self.candidates[key].pos_pattern.append(pos)
        self.candidates[key].sent_id.append(sentence_id)
        self.candidates[key].raw_form.append(words)

    def filter_candidates(self):
        stopwords = list()
        if self.lang == 'ko':
            with open('stopwords-ko.txt', 'r') as f:
                stopwords = f.readlines()
                stopwords = [word.strip() for word in stopwords]
        elif self.lang == 'en':
            ### TODO ###
            stopwords = list()
        else:
            log.warning('No stopwords for {}'.format(convert(self.lang)))
        for key in list(self.candidates):
            if len(key) < 3:
                self.candidates.pop(key, None)
            elif len(key.split()) > MAX_TOKEN or len(key.split()) < MIN_TOKEN:
                self.candidates.pop(key, None)
            elif key in stopwords:
                self.candidates.pop(key, None)
            elif helper.check_news_stopwords(key):
                self.candidates.pop(key, None)
            elif helper.check_user_stopwords(key):
                self.candidates.pop(key, None)

    def make_graph(self):
        t = [topic[-1] for topic in self.topics]
        log.debug(f'topics: {t}')
        for i in range(len(t)):
            for j in range(len(t)):
                self.graph.add_edge(t[i], t[j], weight=0.0)
                for c_i in self.topics[i]:
                    for c_j in self.topics[j]:
                        for pos_i in self.candidates[c_i].offsets:
                            for pos_j in self.candidates[c_j].offsets:
                                gap = abs(pos_i - pos_j)
                                if pos_i > pos_j:
                                    gap = gap - (len(c_j) + 1)
                                if pos_j > pos_i:
                                    gap = gap - (len(c_i) + 1)
                                if gap == 0:
                                    continue
                                self.graph[t[i]][t[j]]['weight'] += 1.0 / gap
        log.debug(self.graph.edges(data=True))

    def make_raw_graph(self):
        c = list(self.candidates.keys())
        for i in range(len(c)):
            for j in range(len(c)):
                self.graph.add_edge(c[i], c[j], weight=0.0)
                for pos_i in self.candidates[c[i]].offsets:
                    for pos_j in self.candidates[c[j]].offsets:
                        gap = abs(pos_i - pos_j)
                        if pos_i > pos_j:
                            gap = gap - (len(c[j]) + 1)
                        if pos_j > pos_i:
                            gap = gap - (len(c[i]) + 1)
                        if gap == 0:
                            continue
                        self.graph[c[i]][c[j]]['weight'] += 1.0 / gap
        log.debug(self.graph.edges(data=True))

    def show_graph(self, threshold=0.1):
        selected_edges = [(u, v, attrs) for u, v, attrs in self.graph.edges(data=True) if attrs['weight'] > threshold]
        G = nx.Graph()        
        G.add_edges_from(selected_edges)
        for _, _, d in G.edges(data=True):
            d['weight'] = round(d['weight'], 3)
        pos = nx.spring_layout(G)
        nx.draw_networkx_nodes(G, pos)
        nx.draw_networkx_labels(G, pos, font_family='NanumSquare', font_size=8, font_weight='bold')
        nx.draw_networkx_edges(G, pos)
        # nx.draw_networkx_edge_labels(G, pos, edge_labels=nx.get_edge_attributes(G, 'weight'), font_size=5)
        plt.show()

    def cluster_topic(self, strategy='average', threshold=1.3):
        candidates = list(self.candidates.keys())
        count = CountVectorizer()
        X = count.fit_transform(candidates)
        Z = linkage(X.toarray(), strategy)
        clusters = fcluster(Z, t=threshold, criterion='distance')
        for cluster_id in range(1, max(clusters) + 1):
            log.debug(f'cluster {cluster_id}: {[candidates[j] for j in range(len(clusters)) if clusters[j] == cluster_id]}')
            self.topics.append([candidates[j] for j in range(len(clusters)) if clusters[j] == cluster_id])

    def topic_ranking(self, strategy='first'):
        w = nx.pagerank_scipy(self.graph, alpha=0.85, weight='weight')
        log.debug(w)
        if not self.cycle:
            wc = WordCloud(
                font_path='C:/Users/komsco/AppData/Local/Microsoft/Windows/Fonts/NanumSquareEB.ttf',
                background_color='white',
                width=600,
                height=400
            ).generate_from_frequencies(w)
            plt.imshow(wc)
            plt.axis('off')
            plt.show()