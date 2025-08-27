import os
from exchange.okx import OKXExchange
from indicators import Strength, TechnicalIndicators
import schedule
import time


okx_client = OKXExchange()
indicators = TechnicalIndicators()
leverage = os.getenv("LEVERAGE", "5")
grid_leverage = os.getenv("GRID_LEVERAGE", "5")
amount = os.getenv("AMOUNT", 200)
grid_amount = os.getenv("GRID_AMOUNT", "300")
def main():
    start_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
    print(f'开始执行策略：{start_time}')
    symbol='BTC-USDT-SWAP'
    data = okx_client.get_kline_data(symbol='BTC-USDT-SWAP',bar='4H')
    df = okx_client.convert_kline_to_dataframe(kline_data=data)
    df = indicators.atr(df)
    atr_value = df['ATR'].iloc[-1] if 'ATR' in df.columns else None
    print(f"当前ATR值: {atr_value}")
    signal = indicators.supertrend_summary(df=df)
    # signal = Signal(trend=1, strength=Strength.STRONG)
    print(f'trend:{signal.trend},strength:{signal.strength}')
    # 持仓逻辑
    if signal.trend == 1:
        okx_client.open_position(symbol=symbol,direction='long',amount=amount,leverage=leverage)
        # 开多网格
        okx_client.open_grid_if_not_exist(symbol=symbol,direction='long',amount=grid_amount,leverage=grid_leverage,atr=atr_value)
    elif signal.trend == -1:
        okx_client.open_position(symbol=symbol,direction='short',amount=amount,leverage=leverage)
        # 开多网格
        okx_client.open_grid_if_not_exist(symbol=symbol,direction='short',amount=grid_amount,leverage=grid_leverage,atr=atr_value)

    if signal.strength == Strength.WEAK:
        # 检查如果 多单网格 或者 空单网格不存在，就开启
        okx_client.open_grid_if_not_exist(symbol=symbol,direction='short',amount=grid_amount,leverage=grid_leverage,atr=atr_value)
        okx_client.open_grid_if_not_exist(symbol=symbol,direction='long',amount=grid_amount,leverage=grid_leverage,atr=atr_value)
        pass
    elif signal.trend == 1:
        # 关闭做空网
        okx_client.close_grid_if_exist(symbol=symbol,direction='short')
        pass
    elif signal.trend == -1:
        okx_client.close_grid_if_exist(symbol=symbol,direction='long')
        pass
    print(f'执行策略结束：{start_time}')

def job():
    try:
        main()
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
