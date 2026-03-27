import pandas as pd
import pandas_ta as ta

from enum import Enum
        
class Strength(Enum):
    STRONG = "Strong"
    WEAK = "Weak"




class Signal:
    def __init__(self, trend: int, strength: Strength, supertrend: float = None, is_reversal: bool = False,before_reversal_supertrend:float = None):
        self.trend = trend  # 趋势
        self.strength = strength  # 趋势强度
        self.supertrend = supertrend  # supertrend值
        self.is_reversal = is_reversal 
        self.before_reversal_supertrend =  before_reversal_supertrend# 是否为转折点（上一个supertrend方向和当前方向不一致）
        

class TechnicalIndicators:
    """技术指标计算类"""
    
    def __init__(self):
        """初始化技术指标计算器"""
        pass
    
    def calculate_supertrend(self, 
                           df: pd.DataFrame, 
                           period: int = 20, 
                           multiplier: float = 4.0) -> pd.DataFrame:
        """
        计算SuperTrend指标（使用pandas-ta内置方法）
        
        Args:
            df: 包含OHLC数据的DataFrame，需要包含 'high', 'low', 'close' 列
            period: ATR周期，默认10
            multiplier: ATR倍数，默认3.0
            
        Returns:
            包含SuperTrend指标的DataFrame
        """
        if df.empty:
            return df
        
        # 确保必要的列存在
        required_columns = ['high', 'low', 'close']
        if not all(col in df.columns for col in required_columns):
            raise ValueError(f"DataFrame必须包含以下列: {required_columns}")
        
        df = df.copy()
        
        # 使用pandas-ta内置的supertrend方法
        supertrend_result = ta.supertrend(
            high=df['high'], 
            low=df['low'], 
            close=df['close'], 
            length=period, 
            multiplier=multiplier
        )
        # 合并结果到原DataFrame
        df = pd.concat([df, supertrend_result], axis=1)
        
        # 重命名列以便使用
        supertrend_col = f'SUPERT_{period}_{multiplier}'
        direction_col = f'SUPERTd_{period}_{multiplier}'
        long_col = f'SUPERTl_{period}_{multiplier}'
        short_col = f'SUPERTs_{period}_{multiplier}'
        
        # 添加简化的列名
        df['supertrend'] = df[supertrend_col]
        df['trend'] = df[direction_col]
        df['supertrend_long'] = df[long_col]
        df['supertrend_short'] = df[short_col]
        
        return df

    def supertrend_summary(self,df: pd.DataFrame) -> Signal:
        df = self.calculate_supertrend(df=df,period=20,multiplier=4.0)
        recent_supertrend_values = df['supertrend'].tail(3)
        print(recent_supertrend_values)
        print(df['supertrend'].iloc[-1])
        print(df['supertrend'].iloc[-2])
        strength = Strength.WEAK if recent_supertrend_values.nunique() == 1 else Strength.STRONG
        supertrend_value = df['supertrend'].iloc[-1]  # 获取最近的supertrend值
        # INSERT_YOUR_CODE
        print(df[['open', 'supertrend', 'trend']])
        is_reversal = (df['trend'].iloc[-2] != df['trend'].iloc[-3]) if len(df) >= 2 else False        
        print(is_reversal)
        return Signal(trend=df['trend'].iloc[-1], strength=strength, supertrend=supertrend_value, is_reversal=is_reversal,before_reversal_supertrend=df['supertrend'].iloc[-3])
    
    def atr(self,df: pd.DataFrame):
        """
        计算平均真实波幅（ATR）指标
        
        Args:
            df: 包含OHLC数据的DataFrame，需要包含 'high', 'low', 'close' 列
            period: ATR周期，默认10
            
        Returns:
            包含ATR指标的DataFrame
        """
        if df.empty:
            return df
        
        # 确保必要的列存在
        required_columns = ['high', 'low', 'close']
        if not all(col in df.columns for col in required_columns):
            raise ValueError(f"DataFrame必须包含以下列: {required_columns}")
        
        df = df.copy()
        
        # 使用pandas-ta内置的atr方法
        atr_result = ta.atr(
            high=df['high'], 
            low=df['low'], 
            close=df['close'], 
            length=14
        )
        
        # 合并结果到原DataFrame
        df['ATR'] = atr_result
        
        return df