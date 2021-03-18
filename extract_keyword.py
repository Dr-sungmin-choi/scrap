import os
import sys
import pandas as pd
import requests
import re
from konlpy.tag import Okt, Kkma
from collections import Counter

def tokenize(raw_list):
    '''
    형태소 분석
    명사만 추출
    '''
    result = []
    okt = Okt()
    kkma = Kkma()
    stopwords = ['조폐공사', '한국조폐공사']
    for line in raw_list:
        # poslist = okt.pos(line, stem=True)
        # poslist = okt.nouns(line)
        poslist = kkma.nouns(line)
        result += [word for word in poslist if word not in stopwords]
    return result

if __name__ == '__main__':
    df = pd.read_csv('preprocessed_result.csv')
    output = pd.DataFrame(columns=['Keyword'])
    cols = {
        'news': df.loc[df['type'] == 'news', ['title', 'description']],
        'blog': df.loc[df['type'] == 'blog', ['title', 'description']],
        'kin': df.loc[df['type'] == 'kin', ['title', 'description']]
    }
    for key, value in cols.items():
        title_list = list(value['title'])
        description_list = list(value['description'])
        title_keyword = tokenize(title_list) # title에서 명사 추출
        description_keyword = tokenize(description_list) # description에서 명사 추출
        title_count = {x:title_keyword.count(x) * 3 for x in title_keyword}
        description_count = {x:description_keyword.count(x) for x in description_keyword}
        total_count = Counter(title_count) + Counter(description_count) # 점수 계산
        output = pd.merge(output, pd.DataFrame(list(total_count.items()), columns=['Keyword', f'Count_{key}']), on='Keyword', how='outer')
    output.fillna(0)
    output['Count_total'] = output['Count_news'] + output['Count_blog'] + output['Count_kin']
    output.to_csv("after_result.csv")
