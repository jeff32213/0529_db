import pymssql
import pandas as pd
import numpy as np
import mplfinance as mpf
from collections import defaultdict

def connect_SQL_server(): pass
def get_data(company, start, end, cursor): pass 
def get_turning_wave(company, start, end, cursor): pass
    
def find_patterns(min_max):
    patterns = defaultdict(list) # In order to append index easily
    
    # Find W Shape / Double Bottoms
    for i in range(5 ,len(min_max)):
        window = min_max.iloc[i - 5:i]

        if ((window.iloc[-1]['start_day'] - window.iloc[0]['start_day']).days) > 180:
            continue

        a, b, c, d, e = window['close_price'].iloc[0:5]

        # 雖然這邊頸線用中間峰值畫水平線，但為了找出比較符合的pattern，還是會比較兩點
        if b < c and d < c and abs(b - d) <= np.mean([b, d]) * 0.02 and a >= c:
            patterns['W'].append(window.index)

    # Find M Shape / Double Tops
    for i in range(5 ,len(min_max)):
        window = min_max.iloc[i - 5:i]

        if ((window.iloc[-1]['start_day'] - window.iloc[0]['start_day']).days) > 180:
            continue

        a, b, c, d, e = window['close_price'].iloc[0:5]

        # 雖然這邊頸線用中間峰值畫水平線，但為了找出比較符合的pattern，還是會比較兩點
        if b > c and d > c and abs(b - d) <= np.mean([b, d]) * 0.02 and a <= c:
            patterns['M'].append(window.index)
    
    return patterns

def prepare_plot_data(df, patterns, type, turning_wave, result):
    
    # no data, assign empty obj
    if len(patterns[type]) == 0:
        result[type] = {}
        result[type]['turning_points'] = []
        result[type]['datepairs'] = []
        result[type]['intervals'] = []
        result[type]['necklines'] = []
        return

    
    # concat index of dots
    indicesList = []
    for indices in patterns[type]:
        indicesList.extend(indices) # use [extend] because we want to concat all of the list

    # for drawing all turning points of each pattern
    turning_points = []
    date = df.index.date
    for i in range(len(date)):
        if str(date[i]) in turning_wave.loc[indicesList, 'start_day'].to_string():
            turning_points.append(df['Close'][i])
        else :
            turning_points.append(np.nan)
    # print(turning_points)

    # for drawing lines of each pattern
    datepairs = []
    dot_amount = patterns[type][0].size # M,W 跟 HS,IHS圖形取的點數量不同
    for indices in patterns[type]:
        for j in range(0, dot_amount - 1):
            # print(indices[j],indices[j + 1])
            datepairs.append((turning_wave.loc[indices[j], 'start_day'], turning_wave.loc[indices[j + 1], 'start_day']))
    # print(datepairs)

    # for framing time interval with 2 vertical lines of each pattern
    # and for saving (date, price) tuple of necklines of each pattern
    #  要用mplfinance的alines 畫出來, 而alines每個點是一對tuple(date, price)
    intervals = []
    necklines = []
    for indices in patterns[type]:
        # -----intervals-----
        start_day = turning_wave.loc[indices[0], 'start_day']
        end_day = turning_wave.loc[indices[-1], 'start_day']
        intervals.append(start_day)
        intervals.append(end_day)

        # -----necklines-----
        # W M 用中間點的價錢  而date要橫跨圖形前後各一個時間點
        # IHS HS 用 c e 兩點  而date要橫跨圖形前後各一個時間點
        if type == 'W' or type =='M':
            price = turning_wave.loc[indices[2], 'close_price']
            # 因為一個圖形畫一個頸線, 所以用dict 包兩個 tuples
            necklines.append([(start_day, price), (end_day, price)])
    # print(intervals)
    # print(necklines)
    

    result[type] = {}
    result[type]['turning_points'] = turning_points
    result[type]['datepairs'] = datepairs
    result[type]['intervals'] = intervals
    result[type]['necklines'] = necklines
    # print(result)


def plot_pattern(type, df, plot_data, datepairs_turning_wave):
    if len(plot_data[type]['turning_points']) == 0:
        mpf.plot(df, type='candle', style='yahoo', mav = (5), volume = True, figsize=(100,30),
                    tlines = [dict(tlines=datepairs_turning_wave, tline_use='close', colors='b', linewidths=5, alpha=0.7)])
        mpf.show
        return
    
    apd = [mpf.make_addplot(plot_data[type]['turning_points'], type='scatter', markersize=200, marker='^', color = 'aqua')] 

    mpf.plot(df, type='candle', style='yahoo', mav = (5), volume = True, addplot = apd, figsize=(100,30),
                        tlines = [dict(tlines=datepairs_turning_wave, tline_use='close', colors='b', linewidths=5, alpha=0.7),
                            dict(tlines=plot_data[type]['datepairs'], tline_use='close', colors='r', linewidths=5, alpha=0.7)],
                        vlines = dict(vlines=plot_data[type]['intervals'], colors='c'),
                        alines = dict(alines=plot_data[type]['necklines'], colors='orange'))
    mpf.show


def main():
    conn = connect_SQL_server()
    cursor = conn.cursor()

    company = '2330'
    day_start = '20210101'
    day_end = '20220228'

    #0522
    df = get_data(company, day_start, day_end, cursor)
    turning_wave = get_turning_wave(company, day_start, day_end, cursor)
    datepairs_turning_wave = [(d1, d2) for d1, d2 in zip(turning_wave['end_day'], turning_wave['start_day'])]

    '''
    輸出轉折波
    mpf.plot(df, type='candle', style='yahoo', mav = (5), volume = True, figsize=(100,30),
                 tlines = [dict(tlines=datepairs_turning_wave, tline_use='close', colors='b', linewidths=5, alpha=0.7)])
    mpf.show
    '''

    #0529
    patterns = find_patterns(turning_wave)
    #print(f'patterns["M"]: {patterns["M"]}')
    #print(patterns)

    plot_data = {} # note that dictionary is mutable
    prepare_plot_data(df, patterns, 'W', turning_wave, plot_data)
    prepare_plot_data(df, patterns, 'M', turning_wave, plot_data)
    # print(plot_data['W'])

    plot_pattern('W', df, plot_data, datepairs_turning_wave)
    plot_pattern('M', df, plot_data, datepairs_turning_wave)

  
  
if __name__ == '__main__':
  main()
