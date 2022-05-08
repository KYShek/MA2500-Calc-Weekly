# -*- coding: UTF-8 -*-
import baostock as bs
import numpy as np
import pandas as pd
import datetime as dt
import requests
import os

SCKEY=os.environ.get('SCKEY')

def send_server(title, text):
    api = "https://sctapi.ftqq.com/{}.send".format(SCKEY)
    content = text.replace('\n','\n\n')
    data = {
            'text':title, #标题
            'desp':content} #内容
    res = requests.post(api, data = data)
    return(res)

def calc_MA2500():
    t=dt.datetime.utcnow()
    t=t+dt.timedelta(hours=8)
    t11=t+dt.timedelta(days=-365*11-3)
    d=t.strftime('%Y-%m-%d')
    d11=t11.strftime('%Y-%m-%d')
    #TIME
    result = pd.DataFrame()
    k = bs.query_history_k_data_plus("sh.000001","date,code,close",start_date=d11, end_date=d,frequency="d", adjustflag="3")
    result=pd.concat([result,k.get_data()],axis=0,ignore_index=True)
    result.date=pd.to_datetime(result.date)
    result=result.sort_values(by='date',ascending=False)
    result=result.reset_index(drop=True)
    #ESSENTIAL DATA
    today=pd.DataFrame()
    today['close']=result.nlargest(2500,'date').close
    MA2500=today.close.astype(float).mean()
    MAdiv=int(MA2500/1.2*100)/100
    MAmul=int((MA2500*1.2)*100)/100
    MA2500=int(MA2500*100)/100
    close_today=int(float(result.loc[0,'close'])*100)/100
    #CALC MA2500
    print(MAdiv)
    print(MA2500)
    print(MAmul)
    print(close_today)
    #
    if(close_today<=MAdiv):
        tilt="今日沪指低于÷1.2线"
    else:
        if(close_today<=MA2500):
            judge="÷1.2"
        elif(close_today<=MAmul):
            judge="MA2500"
        else:
            judge="*1.2"
        tilt="今日沪指高于"+judge+"线"

    #GENERATE TITLE
    # 斜杠用来代码换行
    cont="今日沪指收盘: "+str(close_today)+"\n今日MA2500数据 \n\t *1.2: "+str(MAmul)+"\n\t 均："+str(MA2500)+"\n\t /1.2: "+str(MAdiv)
    test_out = cont.replace('\n','\n\n')

    return tilt, cont

def main():
    title = "每周MA2500计算服务异常"
    text = "登录获取股市数据失败"

    try:
        # login boastock server first
        lg = bs.login()
        if (lg.error_code == '0'):
            title, text = calc_MA2500()
            # logout at last
            bs.logout
    except Exception:
        print(Exception)

    print(title)
    print(text)
    send_server(title, text)

if __name__ == '__main__':
    main()
