# 配置文件
class Config:
    # 基础配置
    DATA_FILE = 'data.xlsx'
    
    # 交易配置从TradingConfig获取，这里保留默认值
    INITIAL_CAPITAL = 10000000
    LEVERAGE = 0
    COMMISSION_RATE = 0.001
    UNIT_SIZE = 1
    MAX_POSITION_SIZE = 100 