from config import Config
from strategies import MACrossStrategy, RSIStrategy
from backtest import Backtest
import pandas as pd
from tabulate import tabulate

class TradingConfig:
    def __init__(self):
        self.INITIAL_CAPITAL = 10000000  # 初始资金
        self.LEVERAGE = 0  # 杠杆
        self.COMMISSION_RATE = 0.001  # 手续费率 0.1%
        self.UNIT_SIZE = 1  # 最小交易单位（1柜）
        self.MAX_POSITION_SIZE = None  # 最大持仓量，None表示不限制

    def calculate_position_size(self, price):
        """计算在当前价格下可以购买的最大数量（考虑手续费）"""
        max_quantity = self.INITIAL_CAPITAL / (price * (1 + self.COMMISSION_RATE))
        return int(max_quantity)  # 向下取整到整数柜

def print_strategy_results(name, metrics):
    print(f"\n{name}策略结果：")
    
    # 分类打印指标
    print("\n基础指标：")
    basic_metrics = ['交易次数', '总收益', '总收益率', '平均收益', '平均收益率', '胜率']
    for metric in basic_metrics:
        if metric in metrics:
            print(f"{metric}: {metrics[metric]}")
    
    print("\n风险指标：")
    risk_metrics = ['最大单笔收益', '最大单笔损失', '收益标准差', '夏普比率', '年化收益率', '年化波动率']
    for metric in risk_metrics:
        if metric in metrics:
            print(f"{metric}: {metrics[metric]}")
    
    # 将交易记录转换为DataFrame并打印
    if '交易记录' in metrics and metrics['交易记录']:
        print("\n交易记录：")
        df = pd.DataFrame(metrics['交易记录'])
        # 格式化数值列
        if not df.empty:
            df['profit'] = df['profit'].map('{:,.2f}'.format)
            df['profit_pct'] = df['profit_pct'].map('{:.2f}%'.format)
            df['entry_price'] = df['entry_price'].map('{:,.2f}'.format)
            df['exit_price'] = df['exit_price'].map('{:,.2f}'.format)
            # 重命名列
            df.columns = ['入场时间', '出场时间', '入场价格', '出场价格', '收益', '收益率']
            print(tabulate(df, headers='keys', tablefmt='pretty', showindex=False))

def save_results_to_md(results, config):
    """
    将策略回测结果保存为Markdown文档
    """
    import datetime
    
    # 创建时间戳
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f'backtest_report_{timestamp}.md'
    
    with open(filename, 'w', encoding='utf-8') as f:
        # 写入标题
        f.write("# 策略回测报告\n\n")
        
        # 写入回测配置
        f.write("## 回测配置\n\n")
        f.write(f"- 初始资金: {config.INITIAL_CAPITAL:,} 元\n")
        f.write(f"- 交易单位: {config.UNIT_SIZE} 柜\n")
        f.write(f"- 最大持仓: {config.MAX_POSITION_SIZE} 柜\n")
        f.write(f"- 手续费率: {config.COMMISSION_RATE*100}%\n\n")
        
        # 写入每个策略的结果
        f.write("## 策略表现\n\n")
        for name, metrics in results.items():
            if not metrics:  # 跳过空结果
                continue
                
            f.write(f"### {name}策略\n\n")
            
            # 基础指标
            if any(metric in metrics for metric in ['交易次数', '总收益', '总收益率', '平均收益', '平均收益率', '胜率']):
                f.write("#### 基础指标\n\n")
                basic_metrics = ['交易次数', '总收益', '总收益率', '平均收益', '平均收益率', '胜率']
                for metric in basic_metrics:
                    if metric in metrics:
                        f.write(f"- {metric}: {metrics[metric]}\n")
                f.write("\n")
            
            # 风险指标
            if any(metric in metrics for metric in ['最大单笔收益', '最大单笔损失', '收益标准差', '夏普比率', '年化收益率', '年化波动率']):
                f.write("#### 风险指标\n\n")
                risk_metrics = ['最大单笔收益', '最大单笔损失', '收益标准差', '夏普比率', '年化收益率', '年化波动率']
                for metric in risk_metrics:
                    if metric in metrics:
                        f.write(f"- {metric}: {metrics[metric]}\n")
                f.write("\n")
            
            # 交易记录
            if '交易记录' in metrics and metrics['交易记录']:
                f.write("#### 交易记录\n\n")
                f.write("| 入场时间 | 出场时间 | 入场价格 | 出场价格 | 收益 | 收益率 |\n")
                f.write("|----------|----------|----------|----------|------|--------|\n")
                for trade in metrics['交易记录']:
                    f.write(f"| {trade['entry_date']} | {trade['exit_date']} | "
                           f"{trade['entry_price']:,.2f} | {trade['exit_price']:,.2f} | "
                           f"{trade['profit']:,.2f} | {trade['profit_pct']:.2f}% |\n")
                f.write("\n")
            
            # 添加策略图表链接
            f.write(f"#### 策略图表\n\n")
            f.write(f"![{name}策略回测结果](strategy_results_{name}.png)\n\n")
            
            # 添加完整交易流水记录
            if '完整交易流水' in metrics:
                f.write("#### 资金状态跟踪\n\n")
                f.write("| 订单号 | 交易时间 | 可用资金 | 持仓市值 | 总资产 | 持仓数量 |\n")
                f.write("|--------|----------|----------|----------|--------|----------|\n")
                
                for status in metrics['资金状态']:
                    f.write(f"| {status['order_id']} | {status['date']} | "
                           f"{status['available_cash']:,.2f} | {status['position_value']:,.2f} | "
                           f"{status['total_value']:,.2f} | {status['position_quantity']} |\n")
                f.write("\n")
                
                f.write("#### 完整交易流水\n\n")
                f.write("| 订单号 | 交易类型 | 交易时间 | 交易价格 | 交易数量 | 交易金额 | 信号强度 | 关联订单 |\n")
                f.write("|--------|----------|----------|----------|----------|----------|----------|----------|\n")
                
                # 遍历所有交易记录
                for trade in metrics['完整交易流水']:
                    trade_type = "买入" if trade['type'] == 'buy' else "卖出"
                    amount = trade.get('cost', trade.get('revenue', 0))
                    signal_str = f"{trade.get('signal_strength', 'N/A'):.2f}" if 'signal_strength' in trade else 'N/A'
                    related_order = trade.get('related_buy_order', '-') if trade['type'] == 'sell' else '-'
                    
                    f.write(f"| {trade['order_id']} | {trade_type} | {trade['date']} | "
                           f"{trade['price']:,.2f} | {trade['quantity']} | "
                           f"{amount:,.2f} | {signal_str} | {related_order} |\n")
                f.write("\n")
            
        # 写入总结
        f.write("## 总结\n\n")
        # 计算并写入策略对比结果
        f.write("### 策略对比\n\n")
        
        # 定义指标映射关系
        metric_mappings = {
            '总收益率': '总收益率(相对初始资金)',  # 使用实际存储的键名
            '胜率': '胜率',
            '夏普比率': '夏普比率',
            '年化收益率': '年化收益率'
        }
        
        comparison_metrics = ['总收益率', '胜率', '夏普比率', '年化收益率']
        f.write("| 策略 | " + " | ".join(comparison_metrics) + " |\n")
        f.write("|------|" + "|".join(["-" * len(m) for m in comparison_metrics]) + "|\n")
        
        for name, metrics in results.items():
            if not metrics:  # 跳过空结果
                continue
            values = []
            for metric in comparison_metrics:
                # 使用映射关系获取正确的键名
                actual_key = metric_mappings.get(metric, metric)
                value = metrics.get(actual_key, 'N/A')
                values.append(str(value))
            f.write(f"| {name} | " + " | ".join(values) + " |\n")
        
    print(f"\n回测报告已保存为: {filename}")

def main(strategies=None, config=None):
    """
    运行回测
    :param strategies: 要运行的策略列表，None表示运行所有策略
    :param config: 交易配置对象
    """
    if config is None:
        config = TradingConfig()
    
    results = {}
    
    # 可用策略配置
    available_strategies = {
        'MA': (MACrossStrategy, {
            'short_window': 5, 
            'long_window': 20,
            'initial_capital': config.INITIAL_CAPITAL,
            'leverage': config.LEVERAGE,
            'commission_rate': config.COMMISSION_RATE,
            'unit_size': config.UNIT_SIZE,
            'max_position_size': config.MAX_POSITION_SIZE
        }),
        'RSI': (RSIStrategy, {
            'period': 10, 
            'overbought': 80, 
            'oversold': 20,
            'initial_capital': config.INITIAL_CAPITAL,
            'leverage': config.LEVERAGE,
            'commission_rate': config.COMMISSION_RATE,
            'unit_size': config.UNIT_SIZE,
            'max_position_size': config.MAX_POSITION_SIZE
        })
    }
    
    # 确定要运行的策略
    if strategies is None:
        strategies = available_strategies.keys()
    elif isinstance(strategies, str):
        strategies = [strategies]
    
    # 运行选定的策略
    for strategy_name in strategies:
        if strategy_name in available_strategies:
            strategy_class, params = available_strategies[strategy_name]
            backtest = Backtest(strategy_class, **params)
            backtest.run()
            backtest.plot_results()
            results[strategy_name] = backtest.performance_metrics
    
    # 打印结果并保存到MD文件
    print("\n=== 策略运行结果 ===")
    for name, metrics in results.items():
        print_strategy_results(name, metrics)
    
    # 保存结果到MD文件
    save_results_to_md(results, config)

if __name__ == "__main__":
    # 创建交易配置
    config = TradingConfig()
    config.INITIAL_CAPITAL = 10000000  # 1000万初始资金
    config.UNIT_SIZE = 1  # 最小交易单位为1柜
    config.MAX_POSITION_SIZE = 100  # 最大持仓100柜（可选）
    
    # 运行策略
    main(['MA', 'RSI'], config)