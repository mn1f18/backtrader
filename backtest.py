import pandas as pd
import numpy as np
from data_loader import DataLoader
from config import Config
import matplotlib
matplotlib.use('Agg')  # 设置后端为Agg
matplotlib.rcParams['font.sans-serif'] = ['SimHei']  # 用来正常显示中文标签
matplotlib.rcParams['axes.unicode_minus'] = False  # 用来正常显示负号
import matplotlib.pyplot as plt
import os

class Backtest:
    def __init__(self, strategy_class, **strategy_params):
        self.data_loader = DataLoader(Config.DATA_FILE)
        self.data = self.data_loader.load_data()
        
        # 检查数据排序
        if not self.data.index.is_monotonic_increasing:
            print("警告：数据未按时间正序排列！")
            self.data.sort_index(inplace=True)
        
        # 保存初始资金和策略名称    
        self.initial_capital = strategy_params.get('initial_capital', Config.INITIAL_CAPITAL)
        self.strategy_name = strategy_class.__name__.replace('Strategy', '')  # 移除'Strategy'后缀
            
        self.strategy = strategy_class(
            data=self.data,
            **strategy_params
        )
        self.trades = []
        self.performance_metrics = {}
        
    def run(self):
        """运行回测"""
        signals = self.strategy.generate_signals()
        self._process_trades(signals)
        self._calculate_metrics()
        
    def _process_trades(self, signals):
        """处理交易"""
        position = 0
        available_cash = self.initial_capital  # 可用资金
        current_position = 0  # 当前持仓数量
        position_value = 0    # 持仓市值
        order_id = 1  # 初始化订单号
        
        # 添加资金状态记录
        self.capital_status = []
        
        for idx in signals.index:
            current_signal = signals.loc[idx]
            if isinstance(current_signal, (pd.Series, pd.DataFrame)):
                current_signal = current_signal.iloc[0]
            
            # 获取当前价格
            current_price = self.data.loc[idx, 'close']
            if isinstance(current_price, (pd.Series, pd.DataFrame)):
                current_price = current_price.iloc[0]
            current_price = float(current_price)
            
            if current_signal > 0 and available_cash > 0:  # 买入信号
                # 使用信号强度计算买入量
                max_quantity = self.strategy.calculate_buy_quantity(current_price, signal_strength=current_signal)
                
                # 检查资金是否足够
                cost = current_price * max_quantity * (1 + self.strategy.commission_rate)
                if cost > available_cash:
                    max_quantity = int(available_cash / (current_price * (1 + self.strategy.commission_rate)))
                
                if max_quantity >= self.strategy.unit_size:
                    cost = current_price * max_quantity * (1 + self.strategy.commission_rate)
                    available_cash -= cost
                    current_position += max_quantity
                    position_value = current_position * current_price
                    
                    # 记录资金状态
                    capital_status = {
                        'date': idx,
                        'order_id': f"ORDER_{order_id:04d}",
                        'available_cash': available_cash,
                        'position_value': position_value,
                        'total_value': available_cash + position_value,
                        'position_quantity': current_position
                    }
                    self.capital_status.append(capital_status)
                    
                    self.trades.append({
                        'order_id': f"ORDER_{order_id:04d}",  # 添加订单号
                        'date': idx,
                        'price': current_price,
                        'type': 'buy',
                        'quantity': max_quantity,
                        'signal_strength': current_signal,
                        'cost': cost,
                        'position_change': max_quantity
                    })
                    order_id += 1  # 递增订单号
            
            elif current_signal < 0 and current_position > 0:  # 卖出信号
                # 确保卖出数量是交易单位的整数倍
                quantity = (current_position // self.strategy.unit_size) * self.strategy.unit_size
                if quantity > 0:
                    revenue = current_price * quantity * (1 - self.strategy.commission_rate)
                    available_cash += revenue
                    current_position -= quantity
                    position_value = current_position * current_price
                    
                    # 记录资金状态
                    capital_status = {
                        'date': idx,
                        'order_id': f"ORDER_{order_id:04d}",
                        'available_cash': available_cash,
                        'position_value': position_value,
                        'total_value': available_cash + position_value,
                        'position_quantity': current_position
                    }
                    self.capital_status.append(capital_status)
                    
                    self.trades.append({
                        'order_id': f"ORDER_{order_id:04d}",  # 添加订单号
                        'date': idx,
                        'price': current_price,
                        'type': 'sell',
                        'quantity': quantity,
                        'revenue': revenue,
                        'position_change': -quantity,
                        'related_buy_order': f"ORDER_{order_id-1:04d}"  # 关联买入订单号
                    })
                    order_id += 1  # 递增订单号
        
    def _calculate_metrics(self):
        """计算策略指标"""
        if not self.trades:
            return
            
        # 保存完整交易流水和资金状态
        self.performance_metrics['完整交易流水'] = self.trades
        self.performance_metrics['资金状态'] = self.capital_status
        
        # 计算基本指标
        self.performance_metrics['交易次数'] = len(self.trades)
        
        # 计算收益
        profits = []  # 直接存储数值
        profit_pcts = []  # 直接存储数值
        trade_records = []  # 存储详细交易记录
        current_position = 0
        entry_price = None
        
        for i in range(len(self.trades)):
            trade = self.trades[i]
            
            if trade['type'] == 'buy':
                entry_price = float(trade['price'])
                current_position = 1
            elif trade['type'] == 'sell' and current_position == 1 and entry_price is not None:
                exit_price = float(trade['price'])
                profit = exit_price - entry_price
                profit_pct = (exit_price - entry_price) / entry_price * 100
                
                # 打印调试信息
                print(f"交易详情:")
                print(f"入场价格: {entry_price}")
                print(f"出场价格: {exit_price}")
                print(f"盈亏: {profit}")
                print(f"盈亏率: {profit_pct}%")
                
                # 存储简单数值
                profits.append(float(profit))
                profit_pcts.append(float(profit_pct))
                
                # 存储详细记录
                trade_records.append({
                    'entry_date': self.trades[i-1]['date'],
                    'exit_date': trade['date'],
                    'entry_price': entry_price,
                    'exit_price': exit_price,
                    'profit': float(profit),
                    'profit_pct': float(profit_pct)
                })
                
                current_position = 0
                entry_price = None
        
        if profits:  # 确保有交易记录
            # 计算收益相关指标
            profit_values = np.array(profits, dtype=float)
            profit_pct_values = np.array(profit_pcts, dtype=float)
            
            # 基础指标计算
            total_profit = float(np.sum(profit_values))
            total_profit_pct = (total_profit / self.initial_capital) * 100  # 相对于初始资金的收益率
            avg_profit = float(np.mean(profit_values))
            avg_profit_pct = float(np.mean(profit_pct_values))  # 每笔交易收益率的平均值
            
            # 添加更多解释性的指标名称
            self.performance_metrics['总收益'] = total_profit
            self.performance_metrics['总收益率(相对初始资金)'] = f"{total_profit_pct:.2f}%"
            self.performance_metrics['平均每笔收益'] = avg_profit
            self.performance_metrics['平均每笔收益率'] = f"{avg_profit_pct:.2f}%"
            
            # 修改胜率计算
            completed_trades = [p for p in profits if p is not None]  # 只计算已完成的交易
            if completed_trades:
                wins = len([p for p in completed_trades if p > 0])
                losses = len([p for p in completed_trades if p < 0])
                total_trades = len(completed_trades)
                
                win_rate = (wins / total_trades) * 100 if total_trades > 0 else 0
                self.performance_metrics['胜率'] = f"{win_rate:.2f}%"
                self.performance_metrics['完整交易数'] = total_trades
                self.performance_metrics['未完成交易数'] = len(self.trades) - (total_trades * 2)  # 每笔完整交易包含买入和卖出
            
            # 添加更详细的统计
            self.performance_metrics['盈利次数'] = len([p for p in profits if p > 0])
            self.performance_metrics['亏损次数'] = len([p for p in profits if p < 0])
            self.performance_metrics['平局次数'] = len([p for p in profits if p == 0])
            
            # 计算风险指标
            self.performance_metrics['最大单笔收益'] = float(np.max(profit_values))
            self.performance_metrics['最大单笔损失'] = float(np.min(profit_values))
            self.performance_metrics['收益标准差'] = float(np.std(profit_values))
            
            # 修改夏普比率计算
            # 1. 计算年化收益率
            annual_return = total_profit_pct  # 年化总收益率
            
            # 2. 计算年化波动率
            annual_volatility = float(np.std(profit_pct_values) * np.sqrt(252))
            
            # 3. 计算夏普比率
            risk_free_rate = 0.025  # 无风险利率 2.5%
            if annual_volatility != 0:
                sharpe_ratio = (annual_return - risk_free_rate) / annual_volatility
            else:
                sharpe_ratio = 0
                
            self.performance_metrics['夏普比率'] = f"{sharpe_ratio:.2f}"
            
            # 添加额外的风险调整收益指标
            annual_return = total_profit_pct  # 使用之前计算的总收益率
            self.performance_metrics['年化收益率'] = f"{annual_return:.2f}%"
            self.performance_metrics['年化波动率'] = f"{float(np.std(profit_pct_values) * np.sqrt(252)):.2f}%"
            
            # 保存详细的交易记录
            self.performance_metrics['交易记录'] = trade_records
    
    def plot_results(self):
        """绘制策略结果"""
        try:
            import os
            
            # 获取当前工作目录
            current_dir = os.getcwd()
            print(f"当前工作目录: {current_dir}")
            
            # 检查数据
            print(f"数据点数量: {len(self.data)}")
            print(f"交易记录数量: {len(self.trades)}")
            
            # 创建图形
            plt.figure(figsize=(15, 8))
            
            # 绘制价格线并检查数据
            print("正在绘制价格线...")
            plt.plot(self.data.index, self.data['close'], label='价格', color='blue', alpha=0.7)
            
            # 添加买卖点标记和数量标注
            buy_dates = []
            buy_prices = []
            buy_quantities = []  # 添加买入数量列表
            sell_dates = []
            sell_prices = []
            sell_quantities = []  # 添加卖出数量列表
            
            print("正在处理交易记录...")
            for trade in self.trades:
                if trade['type'] == 'buy':
                    buy_dates.append(trade['date'])
                    buy_prices.append(trade['price'])
                    buy_quantities.append(trade['quantity'])
                else:
                    sell_dates.append(trade['date'])
                    sell_prices.append(trade['price'])
                    sell_quantities.append(trade['quantity'])
            
            print(f"买入点数量: {len(buy_dates)}")
            print(f"卖出点数量: {len(sell_dates)}")
            
            # 绘制买入点和数量标注
            if buy_dates:
                plt.scatter(buy_dates, buy_prices, color='green', marker='^', 
                          s=100, label='买入点', zorder=5)
                # 添加买入数量标注
                for i, (date, price, qty) in enumerate(zip(buy_dates, buy_prices, buy_quantities)):
                    plt.annotate(f'{qty}柜', 
                               xy=(date, price),
                               xytext=(10, 10),
                               textcoords='offset points',
                               color='green',
                               fontsize=10,  # 增大字体
                               weight='bold',  # 加粗
                               bbox=dict(facecolor='white',  # 添加白色背景
                                       edgecolor='green',
                                       alpha=0.7,
                                       boxstyle='round,pad=0.5'))
            
            # 绘制卖出点和数量标注
            if sell_dates:
                plt.scatter(sell_dates, sell_prices, color='red', marker='v', 
                          s=100, label='卖出点', zorder=5)
                # 添加卖出数量标注
                for i, (date, price, qty) in enumerate(zip(sell_dates, sell_prices, sell_quantities)):
                    plt.annotate(f'{qty}柜', 
                               xy=(date, price),
                               xytext=(10, -20),
                               textcoords='offset points',
                               color='red',
                               fontsize=10,  # 增大字体
                               weight='bold',  # 加粗
                               bbox=dict(facecolor='white',  # 添加白色背景
                                       edgecolor='red',
                                       alpha=0.7,
                                       boxstyle='round,pad=0.5'))
            
            # 设置图形格式
            plt.title(f'{self.strategy_name}策略回测结果', fontsize=12)
            plt.xlabel('日期', fontsize=10)
            plt.ylabel('价格', fontsize=10)
            plt.grid(True, alpha=0.3)
            plt.legend(loc='best')
            
            # 调整x轴日期显示
            plt.gcf().autofmt_xdate()
            
            # 使用完整路径保存图片
            file_name = f'strategy_results_{self.strategy_name}.png'
            save_path = os.path.join(current_dir, file_name)
            print(f"尝试保存图片到: {save_path}")
            
            # 确保在保存前关闭之前的图形
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            plt.close('all')  # 关闭所有图形
            
            if os.path.exists(save_path):
                print(f"\n{self.strategy_name}策略图表已成功保存为: {save_path}")
                # 打印文件大小
                file_size = os.path.getsize(save_path)
                print(f"文件大小: {file_size/1024:.2f} KB")
            else:
                print(f"\n警告：图表文件未能成功创建: {save_path}")
            
        except Exception as e:
            print(f"绘图错误: {e}")
            import traceback
            print(traceback.format_exc()) 