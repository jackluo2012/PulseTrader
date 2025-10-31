import tushare as ts
import pandas as pd
import os
from dotenv import load_dotenv
# 在类初始化之前加载.env文件
load_dotenv("config/.env")

class TushareDataSource:
    def __init__(self):
        token = os.getenv('TUSHARE_TOKEN')
        if not token:
            raise ValueError("请设置TUSHARE_TOKEN环境变量")
        ts.set_token(token)
        self.pro = ts.pro_api()

    def get_data(self, symbol: str, start: str, end: str):
        df = self.pro.daily(ts_code=symbol, start_date=start, end_date=end)
        df['trade_date'] = pd.to_datetime(df['trade_date'])
        return df.sort_values('trade_date').set_index('trade_date')[['open','high','low','close','vol']]

    def latest_price(self, symbol: str):
        df = self.get_data(symbol, "20240101", "20241231")
        return df['close'].iloc[-1]