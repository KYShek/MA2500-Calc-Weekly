# -*- coding: UTF-8 -*-
import baostock as bs
import numpy as np
import pandas as pd
import datetime as dt
import requests
import os
import json

DDING_KEY=os.environ.get('DDING_KEY')

def send_dingding_msg(msg, timeout=5):
    if not DDING_KEY:
        print("\nWarning: 钉钉消息无法发送，请设置sendkey!")
        return
    access_token = DDING_KEY
    headers = {
        'Content-Type': "application/json"
    }
    url = "https://oapi.dingtalk.com/robot/send"
    querystring = {"access_token":access_token}
    content = {
        "msgtype": "text",
        "text": {
            "content": msg
        }
    }
    try:
        response = requests.post(url, data=json.dumps(content), headers=headers, params=querystring, timeout=timeout)
        print(f'dingding send :{response.text}')
    except Exception as e:
        print(f'dingding msg err:{e}')

def get_stock_code_name(stock_code):
    # 获取证券基本资料
    rs = bs.query_stock_basic(code=stock_code)
    # rs = bs.query_stock_basic(code_name="浦发银行")  # 支持模糊查询

    # 打印结果集
    data_list = []
    while (rs.error_code == '0') & rs.next():
        # 获取一条记录，将记录合并在一起
        data_list.append(rs.get_row_data())
    result = pd.DataFrame(data_list, columns=rs.fields)
    return result.loc[0,'code_name']

def calc_MA2500(stock_code):
    t = dt.datetime.utcnow()
    t = t + dt.timedelta(hours=8)               # 当前的北京时间
    t11 = t + dt.timedelta(days=-365*11-3)      # 得到11年前的时间，减去3个闰年
    d = t.strftime('%Y-%m-%d')
    d11 = t11.strftime('%Y-%m-%d')
    #TIME
    result = pd.DataFrame()

    stock_name = get_stock_code_name(stock_code)
    # 得到三栏的表格: date日期, code证卷代码, close收盘的点数。
    k = bs.query_history_k_data_plus(stock_code,"date,code,close",start_date=d11, end_date=d,frequency="d", adjustflag="3")
    # 得到k线数据
    result = pd.concat([result,k.get_data()],axis=0,ignore_index=True)
    result.date = pd.to_datetime(result.date)
    result = result.sort_values(by='date',ascending=False)        # 按日期排序，今天日期放在最上面
    result = result.reset_index(drop=True)

    today = pd.DataFrame()
    # 得到最近2500天的收盘点数列表
    today['close'] = result.nlargest(2500,'date').close
    # 计算MA2500均值
    MA2500 = today.close.astype(float).mean()
    # 计算MA2500的上下约20%的浮动区间, 并且只取两位小数
    MAdiv = int(MA2500/1.2*100)/100
    MAmul = int((MA2500*1.2)*100)/100
    MA2500 = int(MA2500*100)/100
    # 今天的收盘
    close_today = int(float(result.loc[0,'close'])*100)/100
    date_today = result.loc[0,'date']
    date_today_str = str(date_today.date()) + ": "

    '''
    # for debug purpose
    print()
    print("{}{}收盘点数: {}".format(date_today_str, stock_name, close_today))
    print("MA2500÷1.2点数: {}".format(MAdiv))
    print("MA2500    点数: {}".format(MA2500))
    print("MA2500x1.2点数: {}".format(MAmul))
    print()
    '''

    # recommend:
    #     低于÷1.2线:   ✔
    #     高于÷1.2线:   ✓
    #     高于MA2500线: =
    #     高于x1.2线:   ✗
    #
    title = ''
    if (close_today <= MAdiv):
        recommend = "+"
        title = "低于 ÷1.2" + ": " + recommend
    else:
        if (close_today <= MA2500):
            judge = "÷1.2"
            recommend = "+"
        elif (close_today <= MAmul):
            judge = "MA2500"
            recommend = "="
        else:
            judge = "*1.2"
            recommend = "-"
        title = "高于 "+judge+ ": " + recommend

    arr = [date_today_str,
        stock_name,
       title,
       "today: "+str(close_today),
       f"today/avg:{round(close_today/MA2500,3)}",
       "*1.2: "+str(MAmul),
       "avg: "+ str(MA2500),
       "/1.2: "  + str(MAdiv)
       ]
    return arr

def main():
    try:
        # login boastock server first
        lg = bs.login()
        if (lg.error_code == '0'):
            STOCK_CODES = os.environ.get('STOCK_CODES')
            if STOCK_CODES == '' or STOCK_CODES is None:
                STOCK_CODES = 'sh.000001 sh.000016 sh.000300 sz.399001 sz.399106 sh.000905 sh.000015'

            result = []
            for code in STOCK_CODES.split():
                output = []
                try:
                    output = calc_MA2500(code)
                except Exception as e:
                    print(Exception, e)
                    output = ["error", str(e)]

                print(code, output)
                result.append(output)

            dding_msg = "SoberBot MA2500\n %s" %(json.dumps(result, indent=4, ensure_ascii=False))
            send_dingding_msg(dding_msg)

            # logout at last
            bs.logout
    except Exception as e:
        print(Exception, e)
        dding_msg = "SoberBot MA2500 send error:" + str(e)
        send_dingding_msg(dding_msg)

if __name__ == '__main__':
    main()

# 以MA2500/1.2线、MA2500均线、MA2500*1.2线、MA2500*1.4线、MA2500*1.6线为区间临界值