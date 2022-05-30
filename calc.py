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

def main():
    try:
        lg = bs.login()
        print('login respond error_code:'+lg.error_code)
        print('login respond  error_msg:'+lg.error_msg)
        #LOGIN
        t=dt.datetime.utcnow()
        t=t+dt.timedelta(hours=8)
        t11=t+dt.timedelta(days=-365*11-3)
        d=t.strftime('%Y-%m-%d')
        d11=t11.strftime('%Y-%m-%d')
        #TIME
        result = pd.DataFrame()
        k = bs.query_history_k_data_plus("sz.399001","date,code,close",start_date=d11, end_date=d,frequency="d", adjustflag="3")
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
            tilt="今日深指低于÷1.2线"
        else:
            if(close_today<=MA2500):
                judge="÷1.2"
            elif(close_today<=MAmul):
                judge="MA2500"
            else:
                judge="*1.2"
            tilt="今日深指高于"+judge+"线"
        print(tilt)
        #GENERATE TITLE
        # 斜杠用来代码换行
        cont="今日深指收盘: "+str(close_today)+"\n今日MA2500数据 \n\t *1.2: "+str(MAmul)+"\n\t 均："+str(MA2500)+"\n\t /1.2: "+str(MAdiv)
        test_out = cont.replace('\n','\n\n')
        print(cont)
        send_server(tilt,cont) #插入在需要推送的地方，我这里的"Her said"是我的标题，msg是我前面爬取的消息'''
        bs.logout
    except Exception:
        error = "服务异常"
        send_server('每周MA2500计算服务异常',error)
        print(error)
        print(Exception)

if __name__ == '__main__':
    main()
