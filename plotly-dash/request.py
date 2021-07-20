import pandas as pd
import numpy as np
import requests
import json
import datetime
import sys
from multiprocessing import Manager, Pool
import time
import parmap
from tqdm import tqdm
import csv

# kakao api
APP_KEY = '58069587d497c89edcc965acce478183'
URL = 'https://dapi.kakao.com/v2/local/geo/coord2regioncode.json'


df = pd.read_csv('../data/지역화폐 가맹점 현황.csv', encoding='euc-kr')
df = df.loc[df['위도'].notnull(), :].drop('데이터기준일자', axis=1)
df[['시군명', '상호명', '업종명(종목명)', '소재지도로명주소', '소재지지번주소']] = df[['시군명', '상호명', '업종명(종목명)', '소재지도로명주소', '소재지지번주소']].astype(str)
manager = Manager()
OUTPUT = manager.list()
input_data = np.array_split(df.loc[:, ['경도', '위도']].values, 10000)
# for i in range(len(input_data)):
#     input_data[i] = [x.tolist() for x in input_data[i]]
total = len(input_data[0])

def json_request(url='', encoding='utf-8', success=None, error=lambda e: print('%s : %s' % (e, datetime.datetime.now()), file=sys.stderr)):
    headers={'Authorization': 'KakaoAK {}'.format(APP_KEY)}
    resp = requests.get(url, headers=headers)
    # print('%s : success for request [%s]' % (datetime.datetime.now(), url))
    return resp.text

# longitude : 경도 127.xxx
def reverse_geocode(pair, error=lambda e: print('%s : %s' % (e, datetime.datetime.now()), file=sys.stderr)):
    longitude = pair[0]
    latitude = pair[1]
    url = '%s?x=%s&y=%s' % (URL, longitude, latitude)

    try:
        json_req = json_request(url=url)
        json_data = json.loads(json_req)
        print (json_data)
        json_doc = json_data.get('documents')[1]
        json_gu = json_doc.get('region_2depth_name')
        json_name = json_doc.get('region_3depth_name')
        json_longitude = json_doc.get('x')
        json_latitude = json_doc.get('y')
        OUTPUT.append([json_longitude, json_latitude, json_gu, json_name])
    except Exception as e:
        json_gu = 'NaN'
        json_name = 'NaN'
        print (e)
        OUTPUT.append([longitude, latitude, json_gu, json_name])

def main():
    pool = Pool(processes=8)
    for _ in tqdm(pool.imap_unordered(reverse_geocode, input_data[0]), total=total):
        pass
    pool.close()
    pool.join()
    # df_output = pd.DataFrame(OUTPUT, columns=['longitude', 'latitude', 'kakao_big_city', 'kakao_small_city'])
    # df = df.loc[df['위도'].notnull(), :].drop('데이터기준일자', axis=1)
    # df[['시군명', '상호명', '업종명(종목명)', '소재지도로명주소', '소재지지번주소']] = df[['시군명', '상호명', '업종명(종목명)', '소재지도로명주소', '소재지지번주소']].astype(str)
    # gu, dong = get_address(df)
    # df['kakao_city_big'] = gu
    # df['kakao_city_small'] = dong

    # # 최종 파일 저장
    with open('../data/custom_store_data.csv', 'w', encoding='UTF-8') as f:
        writer = csv.writer(f) 
        writer.writerows(OUTPUT)

    # df_output.to_csv('../data/custom_store_data.csv', encoding='euc-kr')

if __name__ == '__main__':
    main()