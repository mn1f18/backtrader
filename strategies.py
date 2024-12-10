import numpy as np
import pandas as pd
from strategy_base import StrategyBase

class MACrossStrategy(StrategyBase):
    def __init__(self, data, initial_capital, leverage, commission_rate, 
                 unit_size=1, max_position_size=None,
                 short_window=5, long_window=20, **kwargs):
        super().__init__(data, initial_capital, leverage, commission_rate,
                        unit_size=unit_size, max_position_size=max_position_size)
        self.short_window = short_window
        self.long_window = long_window
        
    def generate_signals(self):
        """改进的双均线策略"""
        # 计算移动平均线
        self.data['SMA_short'] = self.data['close'].rolling(window=self.short_window).mean()
        self.data['SMA_long'] = self.data['close'].rolling(window=self.long_window).mean()
        
        # 计算价格动量
        self.data['momentum'] = self.data['close'].pct_change(periods=self.short_window)
        
        # 计算波动率
        self.data['volatility'] = self.data['close'].pct_change().rolling(window=self.short_window).std()
        
        # 生成信号
        signals = pd.Series(0, index=self.data.index)
        
        # 计算信号强度
        signal_strength = abs(self.data['SMA_short'] - self.data['SMA_long']) / self.data['SMA_long']
        signal_strength = signal_strength / signal_strength.max()  # 归一化到0-1
        
        # 买入条件：短期均线上穿长期均线，且动量为正
        buy_condition = (self.data['SMA_short'] > self.data['SMA_long']) & (self.data['momentum'] > 0)
        
        # 卖出条件：短期均线下穿长期均线，或者波动率过高
        sell_condition = (self.data['SMA_short'] < self.data['SMA_long']) | \
                        (self.data['volatility'] > self.data['volatility'].mean() * 2)
        
        signals.loc[buy_condition] = signal_strength[buy_condition]
        signals.loc[sell_condition] = -1
        
        return signals

class RSIStrategy(StrategyBase):
    def __init__(self, data, initial_capital, leverage, commission_rate,
                 unit_size=1, max_position_size=None,
                 period=14, overbought=80, oversold=20, **kwargs):
        super().__init__(data, initial_capital, leverage, commission_rate,
                        unit_size=unit_size, max_position_size=max_position_size)
        self.period = period
        self.overbought = overbought
        self.oversold = oversold
        
    def generate_signals(self):
        """改进的RSI策略"""
        # 计算RSI
        delta = self.data['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=self.period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=self.period).mean()
        rs = gain / loss
        self.data['RSI'] = 100 - (100 / (1 + rs))
        
        # 生成信号
        signals = pd.Series(0, index=self.data.index)
        
        # 计算信号强度
        buy_strength = (self.oversold - self.data['RSI']) / self.oversold  # RSI越低，买入信号越强
        sell_strength = (self.data['RSI'] - self.overbought) / (100 - self.overbought)  # RSI越高，卖出信号越强
        
        # 买入条件：RSI低于超卖线
        buy_condition = self.data['RSI'] < self.oversold
        signals.loc[buy_condition] = buy_strength[buy_condition].clip(0, 1)
        
        # 卖出条件：RSI高于超买线
        sell_condition = self.data['RSI'] > self.overbought
        signals.loc[sell_condition] = -1
        
        return signals 

class CustomStrategy(StrategyBase):
    def __init__(self, data, initial_capital, leverage, commission_rate,
                 unit_size=1, max_position_size=None, **kwargs):
        """
        自定义多因子策略框架
        :param data: 价格数据（日频）
        :param initial_capital: 初始资金
        :param leverage: 杠杆
        :param commission_rate: 手续费率
        :param unit_size: 最小交易单位
        :param max_position_size: 最大持仓量
        :param kwargs: 其他自定义参数
        """
        super().__init__(data, initial_capital, leverage, commission_rate,
                        unit_size=unit_size, max_position_size=max_position_size)
        # 存储不同频率的数据
        self.daily_data = self.data  # 日频数据
        self.weekly_data = None      # 周频数据
        self.monthly_data = None     # 月频数据
        
        # 存储不同类型的因子
        self.technical_factors = {}   # 技术面因子
        self.fundamental_factors = {} # 基本面因子
        self.market_factors = {}      # 市场因子
        
        # 用户自定义参数
        self.custom_params = kwargs
        
    def load_fundamental_data(self, inventory_data=None, basis_data=None, 
                            trade_data=None, macro_data=None):
        """
        加载基本面数据
        :param inventory_data: 库存数据 DataFrame
        :param basis_data: 期现价差数据 DataFrame
        :param trade_data: 进出口数据 DataFrame
        :param macro_data: 宏观数据 DataFrame
        """
        # 存储原始数据
        self.fundamental_raw_data = {
            'inventory': inventory_data,
            'basis': basis_data,
            'trade': trade_data,
            'macro': macro_data
        }
        
    def calculate_technical_factors(self):
        """计算技术面因子"""
        # 趋势类因子
        self.technical_factors['trend'] = {
            'ma20': self.data['close'].rolling(window=20).mean(),
            'ma60': self.data['close'].rolling(window=60).mean(),
            'momentum': self.data['close'].pct_change(periods=5)
        }
        
        # 波动率类因子
        self.technical_factors['volatility'] = {
            'daily_vol': self.data['close'].pct_change().rolling(window=10).std(),
            'weekly_vol': self.data['close'].pct_change().rolling(window=5*10).std()
        }
        
    def calculate_fundamental_factors(self):
        """计算基本面因子"""
        if self.fundamental_raw_data.get('inventory'):
            # 库存因子
            self.fundamental_factors['inventory'] = {
                'level': None,  # 库存水平
                'change': None, # 库存变化
                'yoy': None    # 同比变化
            }
            
        if self.fundamental_raw_data.get('basis'):
            # 期现价差因子
            self.fundamental_factors['basis'] = {
                'spread': None,     # 价差
                'percentage': None  # 价差率
            }
            
        if self.fundamental_raw_data.get('trade'):
            # 贸易因子
            self.fundamental_factors['trade'] = {
                'net_import': None,  # 净进口量
                'yoy_change': None   # 同比变化
            }
            
    def calculate_market_factors(self):
        """计算市场因子"""
        # 市场情绪因子
        self.market_factors['sentiment'] = {
            'rsi': None,    # RSI
            'macd': None    # MACD
        }
        
        # 成交量因子
        self.market_factors['volume'] = {
            'volume_ma': None,     # 成交量均线
            'volume_ratio': None   # 量比
        }
        
    def align_multi_frequency_data(self):
        """对齐不同频率的数据"""
        # 将不同频率的数据对齐到日频
        pass
        
    def calculate_factors(self):
        """
        计算所有因子
        """
        # 对齐数据
        self.align_multi_frequency_data()
        
        # 计算各类因子
        self.calculate_technical_factors()
        self.calculate_fundamental_factors()
        self.calculate_market_factors()
        
        # 因子预处理
        self.process_factors()
        
    def process_factors(self):
        """
        因子预处理：标准化、去极值、补充缺失值等
        """
        pass
        
    def combine_factors(self):
        """
        因子合成
        可以实现因子加权、因子打分等逻辑
        """
        pass
        
    def generate_signals(self):
        """
        生成交易信号
        """
        # 计算因子
        self.calculate_factors()
        
        # 合成因子
        self.combine_factors()
        
        # 生成信号
        signals = pd.Series(0, index=self.data.index)
        
        # 多因子组合信号示例（保留框架）
        try:
            # 1. 技术面信号
            tech_signal = pd.Series(0, index=self.data.index)
            if self.technical_factors.get('trend'):
                trend_ma20 = self.technical_factors['trend']['ma20']
                trend_ma60 = self.technical_factors['trend']['ma60']
                momentum = self.technical_factors['trend']['momentum']
                
                # 技术面信号强度计算（示例）
                tech_strength = abs(trend_ma20 - trend_ma60) / trend_ma60
                tech_strength = tech_strength / tech_strength.max()  # 归一化到0-1
                
            # 2. 基本面信号
            fund_signal = pd.Series(0, index=self.data.index)
            if self.fundamental_factors.get('inventory'):
                # 基本面信号强度计算（预留）
                pass
                
            # 3. 市场信号
            market_signal = pd.Series(0, index=self.data.index)
            if self.market_factors.get('sentiment'):
                # 市场信号强度计算（预留）
                pass
            
            # 4. 信号合成（预留自定义权重）
            # weights = {
            #     'technical': 0.4,
            #     'fundamental': 0.4,
            #     'market': 0.2
            # }
            # final_signal = (
            #     weights['technical'] * tech_signal +
            #     weights['fundamental'] * fund_signal +
            #     weights['market'] * market_signal
            # )
            
            # 5. 信号阈值和方向（预留）
            # signals.loc[final_signal > upper_threshold] = 1
            # signals.loc[final_signal < lower_threshold] = -1
            
            # 6. 信号强度调整（预留）
            # signals = signals * signal_strength
            
        except Exception as e:
            print(f"信号生成错误: {e}")
            return pd.Series(0, index=self.data.index)
        
        return signals
    
    def calculate_position_size(self, signal_strength, current_price):
        """
        计算交易数量
        :param signal_strength: 信号强度 (-1 到 1)
        :param current_price: 当前价格
        :return: 交易数量（正数表示买入，负数表示卖出）
        """
        # 在这里实现您的仓位管理逻辑
        # 示例：
        # 1. 基于信号强度的仓位
        # position_size = max_position * signal_strength
        
        # 2. 基于风险的仓位
        # position_size = risk_capital / (current_price * volatility)
        
        # 3. 基于资金管理的仓位
        # position_size = available_capital * position_ratio
        
        return 0  # 返回计算得到的交易数量