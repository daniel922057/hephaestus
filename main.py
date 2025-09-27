import os
from exchange.okx import OKXExchange
from indicators import Strength, TechnicalIndicators
import schedule
import time


okx_client = OKXExchange()
indicators = TechnicalIndicators()
leverage = int(os.getenv("LEVERAGE", "5"))
grid_leverage = int(os.getenv("GRID_LEVERAGE", "5"))
amount = float(os.getenv("AMOUNT", "200"))
grid_amount = float(os.getenv("GRID_AMOUNT", "300"))
symbol='BTC-USDT-SWAP'
def main():
    start_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
    print(f'开始执行策略：{start_time}')
    data = okx_client.get_kline_data(symbol='BTC-USDT-SWAP',bar='4H')
    df = okx_client.convert_kline_to_dataframe(kline_data=data)
    df = indicators.atr(df)
    atr_value = df['ATR'].iloc[-1] if 'ATR' in df.columns else None
    print(f"当前ATR值: {atr_value}")
    signal = indicators.supertrend_summary(df=df)
    supertrend = signal.supertrend
    # signal = Signal(trend=1, strength=Strength.STRONG)
    print(f'trend:{signal.trend},strength:{signal.strength},supertrend:{supertrend}')
    # 持仓逻辑
    if signal.trend == 1:
        okx_client.open_position(symbol=symbol,direction='long',amount=amount,leverage=leverage,slTriggerPx=supertrend)
        # 开多网格
        okx_client.open_grid_if_not_exist(symbol=symbol,direction='long',amount=grid_amount,leverage=grid_leverage,atr=atr_value)
        #关闭做空网格
        okx_client.close_grid_if_exist(symbol=symbol,direction='short')
    elif signal.trend == -1:
        okx_client.open_position(symbol=symbol,direction='short',amount=amount,leverage=leverage,slTriggerPx=supertrend)
        # 开空网格
        okx_client.open_grid_if_not_exist(symbol=symbol,direction='short',amount=grid_amount,leverage=grid_leverage,atr=atr_value)
        # 关闭做多网格
        okx_client.close_grid_if_exist(symbol=symbol,direction='long')

    print(f'执行策略结束：{start_time}')
def check_stop():
    start_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
    print(f'开始检查止损：{start_time}')
    data = okx_client.get_kline_data(symbol='BTC-USDT-SWAP',bar='4H')
    df = okx_client.convert_kline_to_dataframe(kline_data=data)
    df = indicators.atr(df)
    atr_value = df['ATR'].iloc[-1] if 'ATR' in df.columns else None
    signal = indicators.supertrend_summary(df=df)
    # 获取最后一根k线的 最高价格和最低价格
    open = df['open'].iloc[-1]
    close = df['close'].iloc[-1]
    diff = abs(close-open)
    print(f"open:{open},close:{close},diff:{diff}")
    if signal.trend == 1 and diff > 2*atr_value and open > close:
        print("波动异常关闭多仓和网格")
        okx_client.close_grid_if_exist(symbol=symbol,direction='long')
        # 关闭多仓
        okx_client.close_position(symbol=symbol,direction='long')
    if signal.trend == -1 and diff > 2*atr_value and close > open:
        print("波动异常关闭空仓和网格")
        okx_client.close_grid_if_exist(symbol=symbol,direction='short')
        # 关闭空仓
        okx_client.close_position(symbol=symbol,direction='short')
    print(f"当前ATR值: {atr_value}")
    pass

def job():
    try:
        main()
    except Exception as e:
        print(f"运行main时发生错误: {str(e)}")
def check_stop_job():
    try:
        check_stop()
    except Exception as e:
        print(f"运行main时发生错误: {str(e)}")     
    

if __name__ == "__main__":
    schedule.every().day.at("00:01").do(job)
    schedule.every().day.at("04:01").do(job)
    schedule.every().day.at("08:01").do(job)
    schedule.every().day.at("12:01").do(job)
    schedule.every().day.at("16:01").do(job)
    schedule.every().day.at("20:01").do(job)
    job()
    while True:
        schedule.run_pending()
        time.sleep(1)
