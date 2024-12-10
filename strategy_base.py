from abc import ABC, abstractmethod

class StrategyBase(ABC):
    def __init__(self, data, initial_capital, leverage, commission_rate, unit_size=1, max_position_size=None):
        self.data = data
        self.initial_capital = initial_capital
        self.leverage = leverage
        self.commission_rate = commission_rate
        self.unit_size = unit_size
        self.max_position_size = max_position_size
        
        self.positions = []
        self.current_position = 0
        self.cash = initial_capital
        self.portfolio_value = initial_capital
        
    @abstractmethod
    def generate_signals(self):
        """生成交易信号"""
        pass
    
    def calculate_metrics(self):
        """计算策略指标"""
        pass
    
    def can_buy(self, price, quantity):
        """检查是否可以买入"""
        # 检查是否符合最小交易单位
        if quantity % self.unit_size != 0:
            return False
            
        # 检查是否超过最大持仓限制
        if self.max_position_size and (self.current_position + quantity) > self.max_position_size:
            return False
            
        # 检查资金是否足够
        cost = price * quantity * (1 + self.commission_rate)
        return self.cash >= cost
        
    def can_sell(self, quantity):
        """检查是否可以卖出"""
        # 检查是否符合最小交易单位
        if quantity % self.unit_size != 0:
            return False
            
        return self.current_position >= quantity
        
    def calculate_buy_quantity(self, price, signal_strength=1.0):
        """
        计算可以买入的数量
        :param price: 当前价格
        :param signal_strength: 信号强度(0-1)，用于调整买入比例
        """
        # 计算基础可买数量
        max_quantity = self.cash / (price * (1 + self.commission_rate))
        
        # 根据信号强度调整买入数量
        target_quantity = max_quantity * signal_strength
        
        # 向下取整到最小交易单位的整数倍
        adjusted_quantity = int(target_quantity / self.unit_size) * self.unit_size
        
        # 考虑持仓限制
        if self.max_position_size:
            remaining_position = self.max_position_size - self.current_position
            adjusted_quantity = min(adjusted_quantity, remaining_position)
        
        # 确保不小于最小交易单位
        if adjusted_quantity < self.unit_size:
            return 0
        
        return adjusted_quantity