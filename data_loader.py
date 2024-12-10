import pandas as pd

class DataLoader:
    def __init__(self, file_path):
        self.file_path = file_path
        
    def load_data(self):
        """加载牛肉价格数据"""
        try:
            df = pd.read_excel(self.file_path)
            # 重命名列以匹配策略代码的预期
            df = df.rename(columns={
                'Date': 'date',
                'RMB_price': 'close'
            })
            
            # 确保价格列为数值类型
            df['close'] = pd.to_numeric(df['close'], errors='coerce')
            
            # 确保日期列为索引并按日期正序排列
            if 'date' in df.columns:
                df['date'] = pd.to_datetime(df['date'])  # 确保日期格式正确
                df.set_index('date', inplace=True)
                df.sort_index(inplace=True)  # 按日期正序排列
                
            # 删除任何包含NaN的行
            df = df.dropna()
            
            # 确保所有数值都是float类型
            df = df.astype(float)
            
            return df
        except Exception as e:
            print(f"数据加载错误: {e}")
            return None 