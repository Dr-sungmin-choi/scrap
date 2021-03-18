import os
import sys
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from wordcloud import WordCloud


def make_barplot(df):
    '''
    막대그래프 생성
    '''
    snsplot = sns.barplot(data=df.sort_values(by='Count_total', ascending=False).iloc[3:23, :], x='Keyword', y='Count_total')
    snsplot.set_title("키워드 총합")
    snsplot.set_xticklabels(snsplot.get_xticklabels(), rotation=45)
    plt.show()
    snsplot = sns.barplot(data=df.sort_values(by='Count_news', ascending=False).iloc[3:23, :], x='Keyword', y='Count_news')
    snsplot.set_title("키워드 뉴스")
    snsplot.set_xticklabels(snsplot.get_xticklabels(), rotation=45)
    plt.show()
    snsplot = sns.barplot(data=df.sort_values(by='Count_blog', ascending=False).iloc[3:23, :], x='Keyword', y='Count_blog')
    snsplot.set_title("키워드 블로그")
    snsplot.set_xticklabels(snsplot.get_xticklabels(), rotation=45)
    plt.show()
    snsplot = sns.barplot(data=df.sort_values(by='Count_kin', ascending=False).iloc[3:23, :], x='Keyword', y='Count_kin')
    snsplot.set_title("키워드 지식in")
    snsplot.set_xticklabels(snsplot.get_xticklabels(), rotation=45)
    plt.show()

def make_wordcloud(df):
    '''
    wordcloud 생성
    '''
    FONT_PATH = '/Library/Fonts/NanumBarunGothic.ttf'
    df_input = df.sort_values(by='Count_total', ascending=False).iloc[3:,:]
    df_input = df_input.groupby('Keyword').Count_total.apply(int).to_dict()
    wordcloud = WordCloud(font_path=FONT_PATH, background_color='white').generate_from_frequencies(df_input)
    plt.imshow(wordcloud, interpolation='bilinear')
    plt.axis("off")
    plt.show()

if __name__ == '__main__':
    plt.style.use('ggplot')
    df = pd.read_csv('after_result.csv')
    sns.set(
        font='AppleGothic',
        rc={'axes.unicode_minus': False},
        style='darkgrid'
    )
    make_barplot(df)
    make_wordcloud(df)