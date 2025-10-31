import pandas as pd

class MACrossStrategy:
    def __init__(self, fast=5, slow=20):
        self.fast = fast
        self.slow = slow

        def generate_signals(self, data):
            """
            生成交易信号
            
            参数:
                data: pandas.DataFrame, 包含价格数据的DataFrame，必须包含'close'列
                
            返回:
                pandas.DataFrame, 包含原始数据以及新增的移动平均线和交易信号的DataFrame
            """
            df = data.copy()
            # 计算快速和慢速移动平均线
            df['ma_fast'] = df['close'].rolling(self.fast).mean()
            df['ma_slow'] = df['close'].rolling(self.slow).mean()
            # 初始化信号列
            df['signal'] = 0
            # 当快速均线大于慢速均线时，生成买入信号(1)
            df.loc[df['ma_fast'] > df['ma_slow'], 'signal'] = 1
            # 当快速均线小于等于慢速均线时，生成卖出信号(-1)
            df.loc[df['ma_fast'] <= df['ma_slow'], 'signal'] = -1
            return df