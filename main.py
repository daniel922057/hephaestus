import os


from exchange.okx import OKXExchange
from indicators import TechnicalIndicators
import schedule
import time


okx_client = OKXExchange()
indicators = TechnicalIndicators()
leverage = int(os.getenv("LEVERAGE", "5"))
grid_leverage = int(os.getenv("GRID_LEVERAGE", "5"))
amount = float(os.getenv("AMOUNT", "500"))
grid_amount = float(os.getenv("GRID_AMOUNT", "300"))
symbol='BTC-USDT-SWAP'
    

def main():
    start_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
    print(f'开始执行策略：{start_time}')
    data = okx_client.get_kline_data(symbol='BTC-USDT-SWAP',bar='4H')
    print(f'data lenth:{len(data)}')
    df = okx_client.convert_kline_to_dataframe(kline_data=data)
    df = indicators.atr(df)
    atr_value = df['ATR'].iloc[-1] if 'ATR' in df.columns else None
    print(f"当前ATR值: {atr_value}")
    signal = indicators.supertrend_summary(df=df)
    supertrend = signal.supertrend
    open = df['open'].iloc[-1]
    print(f'open:{open}')
    last_kline_diff = df['close'].iloc[-2] -  df['open'].iloc[-2]
    print(last_kline_diff)
    print(f'trend:{signal.trend},strength:{signal.strength},supertrend:{supertrend}')
    # 获取当前价格和 supertrend 差 绝对值
    # 获取最新价格
    # current_price = df['close'].iloc[-1]
    price = df['high'].iloc[-2] if signal.trend == 1 else  df['low'].iloc[-2]
    supertrend_diff_abs = abs(price - supertrend)
    print(f"上一高点或低点: {price}，supertrend: {supertrend}，差的绝对值: {supertrend_diff_abs}")
    print(f"2倍ATR值: {2 * atr_value},supertrend*2%:{supertrend * 0.025}")
    allow_open = (supertrend_diff_abs < 2 * atr_value) or supertrend_diff_abs < supertrend * 0.025
    if signal.is_reversal:
        supertrend_diff_abs = abs(open - signal.before_reversal_supertrend)
        print(f"[转折信号] 当前K线open: {open}，上次反转前supertrend: {signal.before_reversal_supertrend}，差的绝对值: {supertrend_diff_abs}")
        allow_open = (supertrend_diff_abs < 2 * atr_value) or supertrend_diff_abs < supertrend * 0.025
        print(f"[转折信号] 开仓判定条件: supertrend_diff_abs < 2 * ATR ({2 * atr_value}) or supertrend_diff_abs < supertrend*2% ({supertrend * 0.025})，allow_open: {allow_open}")
        okx_client.open_position(symbol=symbol,direction='long' if signal.trend ==1 else 'short',amount=amount*0.1,leverage=leverage,supertrend=supertrend,atr=atr_value,allow_open=allow_open)
        # 如果没有中性网格开一个
        okx_client.open_grid_if_not_exist(symbol=symbol,direction='neutral',amount=grid_amount,leverage=grid_leverage,atr=atr_value,supertrend=supertrend) 
        #关闭趋势网格
        okx_client.close_grid_if_exist(symbol=symbol,direction = 'short' if signal.trend ==1 else 'long')
        return
    position = okx_client.get_positions(symbol=symbol)
    print(f"仓位:{position}")
    # 如果没有仓位 挂单
    direction = 'long' if signal.trend ==1 else 'short'
    if not position or float(position['pos']) == 0:
        # INSERT_YOUR_CODE
        print(f"未持仓，准备挂单，信号方向: {direction}，价格: {price}，允许开仓: {allow_open}")
        okx_client.close_pending_grid_if_exist(symbol=symbol,direction='long' if signal.trend ==1 else 'short')
        if allow_open:
            # INSERT_YOUR_CODE
            print(f"挂单条件满足，准备委托下单: symbol={symbol}, direction={direction}, price={price}, amount={amount*0.3}")
            okx_client.place_limit_order(symbol=symbol,direction='long' if signal.trend ==1 else 'short',price=price,amount=amount*0.3,leverage=leverage)
            okx_client.open_grid_if_not_exist(symbol=symbol,direction='long' if signal.trend ==1 else 'short',amount=grid_amount,leverage=grid_leverage,atr=atr_value,supertrend=supertrend,triggerPx=price) 
            return
        else:
            # INSERT_YOUR_CODE
            okx_client.cancel_trigger_orders(symbol=symbol)
            print(f"挂单条件不满足，上一高点或低点: {price}，supertrend: {supertrend}，差的绝对值: {supertrend_diff_abs}，2倍ATR值: {2 * atr_value}")
            return
    # 检查仓位是是否是满仓 》 50% 投资金额
    if float(position['imr']) > 0.7 * amount:
        # INSERT_YOUR_CODE
        okx_client.cancel_trigger_orders(symbol=symbol)
        # 满仓 超级趋势价格已经逾越开仓价格
        if (signal.trend == 1 and signal.supertrend > float(position['avgPx'])) or (signal.trend == -1 and signal.supertrend < float(position['avgPx'])):
            okx_client.cancel_stop_loss_order(symbol=symbol)
            okx_client.update_safe_stop_price(symbol=symbol,low=df['low'].iloc[-2],high=df['high'].iloc[-2],atr=atr_value,direction=direction,supertrend=supertrend)
        else:
            print(f"已满仓（大于70%仓位），仅更新止损价。当前持仓: {position['imr']}，阈值: {0.7 * amount}")
            okx_client.update_stop_price(symbol=symbol,frame_open_price=open,atr=atr_value,direction=direction,sz=abs(float(position['pos'])),supertrend=supertrend)
        return
    else:
        # INSERT_YOUR_CODE
        print(f"未满仓，当前持仓: {position['imr']}，计划挂单金额: {amount*0.5}，计划价格: {price}，信号方向: {direction}，允许开仓: {allow_open}")
    # 准备挂单加仓
    # INSERT_YOUR_CODE
    print(f"准备挂单加仓，当前持仓: {position['imr']}，计划加仓金额: {amount*0.5}，计划价格: {price}，信号方向: {direction}，允许开仓: {allow_open}")
    

    okx_client.close_pending_grid_if_exist(symbol=symbol,direction='long' if signal.trend ==1 else 'short')
    #开启趋势网格
    if allow_open:    
        okx_client.open_grid_if_not_exist(symbol=symbol,direction='long' if signal.trend ==1 else 'short',amount=grid_amount,leverage=grid_leverage,atr=atr_value,supertrend=supertrend,triggerPx=price) 
    
    
    
    allow_add_position = False
    if (signal.trend == 1 and signal.supertrend > float(position['avgPx'])) or (signal.trend == -1 and signal.supertrend < float(position['avgPx'])):
        # INSERT_YOUR_CODE
        print(f"允许加仓条件判断: trend={signal.trend}, supertrend={signal.supertrend}, 持仓均价={position['avgPx']}")
        allow_add_position = True
        # 关闭中性网格
        okx_client.close_grid_if_exist(symbol=symbol,direction = 'neutral')
    else:
    # INSERT_YOUR_CODE
        print(f"不允许加仓，当前趋势: {signal.trend}，supertrend: {signal.supertrend}，持仓均价: {position['avgPx']}")
        okx_client.update_stop_price(symbol=symbol,frame_open_price=open,atr=atr_value,direction=direction,sz=abs(float(position['pos'])),supertrend=supertrend)
    

    if allow_open and allow_add_position:
        # INSERT_YOUR_CODE
        add_position_amount = amount*0.5
        if float(position['imr']) < 0.2 * amount:
            add_position_amount = amount*0.7

        print(f"[加仓] 满足挂单条件 | 当前持仓IMR: {position['imr']} | 加仓金额: {add_position_amount} | 计划价格: {price} | 方向: {direction}")
        okx_client.update_stop_price(symbol=symbol,frame_open_price=open,atr=atr_value,direction=direction,sz=abs(float(position['pos'])),supertrend=supertrend)
        okx_client.place_limit_order(symbol=symbol,direction='long' if signal.trend ==1 else 'short',price=price,amount=add_position_amount,leverage=leverage)
        
    elif allow_open and  float(position['imr']) < 0.2 * amount:
        print(f"[加仓] 满足挂单条件 加仓两层 | 当前持仓IMR: {position['imr']} | 加仓金额: {amount*0.2} | 计划价格: {price} | 方向: {direction}")
        # 挂单两层
        okx_client.update_stop_price(symbol=symbol,frame_open_price=open,atr=atr_value,direction=direction,sz=abs(float(position['pos'])),supertrend=supertrend)
        okx_client.place_limit_order(symbol=symbol,direction='long' if signal.trend ==1 else 'short',price=price,amount=amount*0.2,leverage=leverage)
    else:
    # INSERT_YOUR_CODE
        okx_client.cancel_trigger_orders(symbol=symbol)
        print(f"加仓挂单条件不满足，上一高点或低点: {price}，supertrend: {supertrend}，差的绝对值: {supertrend_diff_abs}，2倍ATR值: {2 * atr_value}")
        okx_client.update_stop_price(symbol=symbol,frame_open_price=open,atr=atr_value,direction=direction,sz=abs(float(position['pos'])),supertrend=supertrend)

def job():
    try:
        main()
        print('===========执行策略结束===============')
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
