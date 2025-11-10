import asyncio
import websockets
import json
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Callable, Optional
from dataclasses import dataclass
import logging
from rich.console import Console
from rich.table import Table

@dataclass
class RealtimeQuote:
    """实时行情数据结构"""
    symbol: str
    price: float
    change: float
    change_pct: float
    volume: int
    timestamp: datetime
    bid_price: float = 0.0
    ask_price: float = 0.0
    bid_volume: int = 0
    ask_volume: int = 0

class RealtimeDataManager:
    """实时数据管理器"""
    
    def __init__(self):
        self.console = Console()
        self.subscribers: Dict[str, List[Callable]] = {}
        self.cache: Dict[str, RealtimeQuote] = {}
        self.is_running = False
        self.update_interval = 3 # 3秒更新一次

    def subscribe(self, symbol: str, callback: Callable[[RealtimeQuote],None]):
        """订阅实时行情数据"""
        if symbol not in self.subscribers:
            self.subscribers[symbol] = []
        self.subscribers[symbol].append(callback)
        self.console.log(f"✅ 订阅 {symbol} 实时行情")
    
    async def unsubscribe(self, symbol: str, callback: Callable):
        """取消订阅实时行情数据"""
        if symbol in self.subscribers:
            self.subscribers[symbol].remove(callback)
            if not self.subscribers[symbol]:
                del self.subscribers[symbol]
            self.console.log(f"❌ 取消订阅 {symbol} 实时行情")
    
    async def get_sina_quote(self, symbol: str) -> Optional[RealtimeQuote]:
        """从新浪获取实时行情数据"""        
        try:
            # 新浪财经接口
            if symbol.endswith('.SZ'):
                sina_symbol = f"sz{symbol.replace('.SZ', '')}"
            elif symbol.endswith('.SH'):
                sina_symbol = f"sh{symbol.replace('.SH', '')}"
            else:
                sina_symbol = symbol
            url = f"https://hq.sinajs.cn/list={sina_symbol}"
            import aiohttp
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as response:
                    text = await response.text(encoding='gbk')
                    
                    if 'var hq_str_' not in text:
                        # 解析 新浪财经数据格式
                        data = text.split('="')[1].split('";')[0].split(',')
                        if len(data) >30:
                            name = data[0]
                            open_price = float(data[1])
                            close_price = float(data[2])
                            current_price = float(data[3])
                            high_price = float(data[4])
                            low_price = float(data[5])
                            volume = int(data[8])
                            bid_price = float(data[11]) if data[11] else 0.0
                            ask_price = float(data[21]) if data[21] else 0.0

                            change = current_price - close_price
                            change_pct = (change / close_price) * 100 if close_price > 0 else 0
                            return RealtimeQuote(
                                symbol=symbol,
                                price=current_price,
                                change=change,
                                change_pct=change_pct,
                                volume=volume,
                                timestamp=datetime.now(),
                                bid_price=bid_price,
                                ask_price=ask_price
                            )
        except Exception as e:
            self.logging.error(f"获取 {symbol} 实时数据失败: {e}")
        return None
    async def update_single_quote(self, symbol: str):
        """更新单个股票的实时行情数据"""
        try:
            quote = await self.get_sina_quote(symbol)
            if quote:
                self.cache[symbol] = quote
                # 通知订阅者
                if symbol in self.subscribers:
                    for callback in self.subscribers[symbol]:
                        callback(quote)
        except Exception as e:
            self.logging.error(f"更新 {symbol} 实时数据失败: {e}")

    def display_quote(self, quote: RealtimeQuote):
        """美化显示实时行情"""
        # 清屏显示新的行情表
        self.console.clear()
        table = Table(title=f"实时行情 -  {quote.symbol}")
        table.add_column("字段", style="cyan",width=12)
        table.add_column("数值", style="white")

        # 价格颜色设置
        price_color = "green" if quote.change >= 0 else "red"

        table.add_row("股票代码", quote.symbol)
        table.add_row("当前价格", f"[{price_color}]{quote.price:.2f}[/{price_color}]")
        table.add_row("涨跌额", f"[{price_color}]{quote.change:+.2f}[/{price_color}]")
        table.add_row("涨跌幅", f"[{price_color}]{quote.change_pct:+.2f}%[/{price_color}]")
        table.add_row("成交量", f"{quote.volume:,}")
        table.add_row("更新时间", quote.timestamp.strftime("%H:%M:%S"))

        self.console.print(table)


    async def start_monitoring(self,symbols: List[str]):
        """启动实时行情监控"""
        self.is_running = True
        self.logger.info(f"开始监控 {len(symbols)} 只股票")

        while self.is_running:
            # 创建一个空列表，用于存储所有的异步任务
            tasks = []
            # 遍历所有的股票符号
            for symbol in symbols:
                # 为每个股票符号创建一个异步任务，用于更新单个股票报价
                task = asyncio.create_task(self.update_single_quote(symbol))
                # 将创建的任务添加到任务列表中
                tasks.append(task)

            # 使用asyncio.gather并发执行所有任务，并捕获可能发生的异常
            await asyncio.gather(*tasks, return_exceptions=True)
            # 在每次更新后等待指定的更新间隔时间
            await asyncio.sleep(self.update_interval)

    def stop_monitoring(self):
        """停止监控"""
        self.is_running = False
        self.logger.info("停止实时数据监控")

    def get_latest_quote(self, symbol: str) -> Optional[RealtimeQuote]:
        """获取最新行情数据"""
        return self.cache.get(symbol)

    def get_all_quotes(self) -> Dict[str, RealtimeQuote]:
        """获取所有缓存的行情数据"""
        return self.cache.copy()