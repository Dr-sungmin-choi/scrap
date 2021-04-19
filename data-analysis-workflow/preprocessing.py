import os
import sys
import pandas as pd
import requests
import re

def clean_text(x):
    '''
    특수기호 제거
    '''
    x = re.sub('<.*?>', '', x)
    x = re.sub('[-=+,ㅣ#\’/\?:;\“”^$.@*\"※~&%·ㆍ!』\\‘|\(\)\[\]\<\>`\'…》↓]', '', x)
    x = re.sub('quot', '', x)
    return x
    
if __name__ == '__main__':
    df = pd.read_csv('crawling_result.csv')
    df['title'] = df['title'].apply(lambda x: clean_text(x)) # title에서 특수기호 제거
    df['description'] = df['description'].apply(lambda x: clean_text(x)) # description에서 특수기호 제거
    df['type'] = 'kin'
    df.loc[df['pubDate'].notnull(), 'type'] = 'news'
    df.loc[df['postdate'].notnull(), 'type'] = 'blog'
    df.drop_duplicates(['title'], keep='first', inplace=True) # 중복 데이터 제거
    df.to_csv("preprocessed_result.csv")
    