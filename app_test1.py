import requests
from datetime import date,datetime
import time
import pandas as pd
import numpy as np
import streamlit as st

def GetKlines(symbol='BTCUSDT',start='2020-8-10',end='2021-8-10',period='1h',base='fapi',v = 'v1'):
    Klines = []
    intervel_map = {'m':60,'h':60*60,'d':24*60*60}
    
    current_temp = int(period[:-1])*intervel_map[period[-1]]
    current_time = int(time.time() // current_temp * current_temp * 1000)
    start_time = int(time.mktime(datetime.strptime(start, "%Y-%m-%d").timetuple()))*1000 + 8*60*60*1000
    
    if end == 'now':
        end_time = current_time
    else:
        end_time = int(time.mktime(datetime.strptime(end, "%Y-%m-%d").timetuple()))*1000 + 8*60*60*1000
        if current_time < end_time:
            end_time = current_time
            # print(1)
            
    
    intervel_sec = int(period[:-1])*intervel_map[period[-1]]
    while start_time < end_time:
        
        mid_time = min(start_time+1000*1000*intervel_sec,end_time)
        # print(start_time)
        url = 'https://'+base+'.binance.com/'+base+'/'+v+'/klines?symbol=%s&interval=%s&startTime=%s&endTime=%s&limit=1000'%(symbol,period,start_time,mid_time)
        res = requests.get(url)
        res_list = res.json()
        if type(res_list) == list and len(res_list) > 0:
            start_time = res_list[-1][0]
            Klines += res_list
            # if len(res_list) == 1:
            #     print(res_list)
        elif type(res_list) == list:
            start_time = start_time+1000*1000*int(period[:-1])*intervel_map[period[-1]]
        else:
            print(url)
    df = pd.DataFrame(Klines,columns=['time','open','high','low','close','amount','end_time','volume','count','buy_amount','buy_volume','null']).astype('float')
    df.index = pd.to_datetime(df.time,unit='ms')
    return df

## 当前交易对
Info = requests.get('https://dapi.binance.com/dapi/v1/exchangeInfo')
symbols = [s['symbol'] for s in Info.json()['symbols']]
# 分离
symbols_nq = list(filter(lambda x:x.split('_')[-1]=='220325', symbols)) #次季合约
symbols_q = list(filter(lambda x:x.split('_')[-1]=='211231', symbols))  #当季合约
symbols_pp = list(filter(lambda x:x.split('_')[-1]=='PERP', symbols))  #USD永续合约
symbols_s = [s.split('_')[0]+'T' for s in symbols_nq] # 现货交易对
','.join(symbols_s)

# K线读取
start_time = '2021-10-1'
end_time = 'now'
#
df_all_nq = pd.DataFrame(index=pd.date_range(start=start_time, end=end_time, freq='1H'),columns=symbols_s)

for i in range(len(symbols_nq)):
    symbol_nq = symbols_nq[i]
    symbol_s = symbols_s[i]
    df_s = GetKlines(symbol=symbol_s,start=start_time,end=end_time,period='1h',base='api',v='v3')
    df_nq = GetKlines(symbol=symbol_nq,start=start_time,end=end_time,period='1h',base='dapi')
    df_all_nq[symbol_s] = (100*(df_nq.close-df_s.close)/df_s.close).drop_duplicates()
df_all_nq = df_all_nq.dropna()
df_end_nq = df_all_nq.iloc[-1]
#
df_all_q = pd.DataFrame(index=pd.date_range(start=start_time, end=end_time, freq='1H'),columns=symbols_s)
for i in range(len(symbols_q)):
    symbol_q = symbols_q[i]
    symbol_s = symbols_s[i]
    df_s = GetKlines(symbol=symbol_s,start=start_time,end=end_time,period='1h',base='api',v='v3')
    df_q = GetKlines(symbol=symbol_q,start=start_time,end=end_time,period='1h',base='dapi')
    df_all_q[symbol_s] = (100*(df_q.close-df_s.close)/df_s.close).drop_duplicates()
df_all_q = df_all_q.dropna()
df_end_q = df_all_q.iloc[-1]

# nq-q
df_all_nq_q = df_all_nq - df_all_q
"""
nq：220325到期\n
q：211231到期
spot：现货
"""
"""
#  1-overall
"""
# df_all.plot(figsize=(16,10),grid=True);
df_table = pd.concat([df_end_nq,df_end_q],axis=1)
df_table = pd.DataFrame(df_table.values, index=df_table.index, columns=['nq','q'])
df_table['nq-q'] = df_table['nq'] - df_table['q']
st.dataframe(df_table,height=1000)  # Same as st.write(df)
"""
#  2: nq-spot
"""
st.line_chart(df_all_nq)
"""
#  3: q-spot
"""
st.line_chart(df_all_q)
"""
#  4: nq-q
"""
st.line_chart(df_all_nq_q)
