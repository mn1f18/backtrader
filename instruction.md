牛肉现货操盘的量化系统，参考backtrader包，但是部分的计算自己实现：


1. 暂时只做现货交易，每一笔买卖的频率是以天为单位（也就是每天的open close价格一样），暂时不考虑日内交易。

2. 运行策略，初始资金 杠杆 和策略 手续费 都要可被预设（暂定初始资金10000000，杠杆0，手续费0.1%），初始给到2个策略

3. 策略的运行结果被记录，包括每一笔交易的成交价格、时间，数量、手续费、盈亏、胜率、盈亏比、最大回撤、夏普比率等。

4. 类似于期货交易系统，策略对比和图像被生成。

5. 代码的最后print下每个策略的运行结果，并做策略的对比，同时生成markdown格式的回测报告。

6. 一个完整的量化的逻辑策略文件（暂不运行，后续会考虑到其他的因子，来做买入和卖出的信号，代码中留个空子给手动操作）

7. 交易规则说明：
   - 只支持做多交易（先买入后卖出）
   - 可以一次性买入后分批卖出
   - 不支持做空（不能先卖出再买入）
   - 每次买入的数量不能超过当前可用资金
   - 每次卖出的数量不能超过当前持仓量
   - 交易数量必须是最小交易单位（1柜）的整数倍
   - 资金使用有严格限制，不允许超过初始资金

8. 策略介绍：
   - **双均线策略 (MACrossStrategy)**：
     - **原理**：利用短期和长期移动平均线的交叉来判断市场趋势。短期均线反映近期价格变化，长期均线反映长期趋势。当短期均线向上穿越长期均线时，表明市场可能进入上升趋势，适合买入；反之则适合卖出。
     - **参数调控**：
       - `short_window`: 短期均线周期，默认为5天。表示计算最近5天的价格平均值，反映短期市场走势。
       - `long_window`: 长期均线周期，默认为20天。表示计算最近20天的价格平均值，反映相对长期的市场趋势。
     - **参数选择说明**：
       - 短期均线(5天)对价格变化更敏感，能够快速反映市场情绪
       - 长期均线(20天)则能够过滤掉短期波动，反映主要趋势
       - 这两个参数可以根据市场特点调整：
         - 缩小间隔(如3/10)会产生更多交易信号，适合波动较大的市场
         - 扩大间隔(如10/30)会减少交易频率，适合趋势性较强的市场

   - **RSI策略 (RSIStrategy)**：
     - **原理**：相对强弱指数（RSI）用于衡量价格变动的速度和变化，帮助识别超买或超卖状态。RSI值在0到100之间，通常低于30被视为超卖，高于70被视为超买。通过这些阈值判断市场的反转点。
     - **参数调控**：
       - `period`: RSI计算周期，默认为14天
       - `overbought`: 超买阈值，默认为70
       - `oversold`: 超卖阈值，默认为30

   - **自定义多因子策略 (CustomStrategy)**：
     - **框架说明**：
       - 支持多维度因子（技术面、基本面、市场面）
       - 支持多频率数据（日、周、月）
       - 提供因子预处理和合成接口
       - 灵活的信号生成机制
       - 支持分批建仓和平仓

9. 回测结果展示：
   - 基础指标（交易次数、总收益、胜率等）
   - 风险指标（最大回撤、夏普比率等）
   - 完整交易流水（包含订单号和关联订单）
   - 资金状态跟踪（可用资金、持仓市值、总资产）
   - 交易图表（带有交易数量标注）

10. 最新更新：
    - 添加了订单号和关联订单跟踪
    - 改进了胜率计算逻辑，区分完整交易和未完成交易
    - 添加了资金状态跟踪
    - 图表显示优化（交易数量标注更醒目）
    - 回测报告格式优化

11. 项目结构说明：

project/
├── config.py # 配置文件，包含基础设置
├── data_loader.py # 数据加载模块
├── strategy_base.py # 策略基类
├── strategies.py # 具体策略实现
├── backtest.py # 回测引擎
├── main.py # 主程序入口
├── requirements.txt # 依赖包列表
├── setup_env.py # 环境设置脚本
├── setup_all.bat # 完整环境设置批处理文件
├── install_packages.bat # 包安装批处理文件
├── activate_venv.bat # 虚拟环境激活脚本
└── data.xlsx # 数据文件