import os
import sys
import pandas as pd
import requests

def make_urls(base_urls, argvs):
    '''
    API 요청할 url 주소를 만드는 함수
    '''
    urls = []
    for url in base_urls.values():
        urls.append(url.format(argvs['encode_type'], argvs['query_word'], argvs['Nstart'], argvs['Ndisplay'], argvs['sort_type']))
    return urls

def crawling(urls, headers):
    '''
    입력받은 url 주소로 API 호출
    urls: API 요청하는 url list
    headers: API 요청 시 필요한 인증 정보
    '''
    df = pd.DataFrame()
    for url in urls:
        request = requests.get(url, headers=headers)    # API 호출
        if (request.status_code == 200):    # 성공 시
            items = pd.DataFrame(request.json()['items'])
            df = pd.concat([df, items])
        else:   # 오류 시
            print("Error code: {}".format(request.status_code))
    return df

if __name__ == '__main__':
    query_word = "한국조폐공사" # 검색할 키워드
    Ndisplay = 100 # 검색 결과 출력 건수
    Nstart = 1 # 검색 시작 위치
    client_id = '7xT5apJ1MOfu4xp4LyfV'
    client_secret = 'xXSwW40yhU'
    base_urls = {
    'news': "https://openapi.naver.com/v1/search/news.{}?query={}&start={}&display={}&sort={}", # 뉴스 url 포맷
    'blog': "https://openapi.naver.com/v1/search/blog.{}?query={}&start={}&display={}&sort={}", # 블로그 url 포맷
    'kin': "https://openapi.naver.com/v1/search/kin.{}?query={}&start={}&display={}&sort={}" # 지식in url 포맷
    }
    headers = { # API 호출할 때 필요한 클라이언트 아이디, 클라이언트 시크릿 전송
        "X-Naver-Client-Id": client_id,
        "X-Naver-Client-Secret": client_secret
    }
    argvs = { # API 요청 변수
        "query_word": query_word,
        "Ndisplay": Ndisplay,
        "Nstart": Nstart,
        "sort_type": 'sim',
        "encode_type":'json'
    }
    urls = make_urls(base_urls, argvs)
    df = crawling(urls, headers)
    df.to_csv("crawling_result.csv") # 수집 결과 저장