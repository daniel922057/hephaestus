import os
from typing import List, Dict, Optional
from okx.MarketData import MarketAPI
from okx.Trade import TradeAPI
from okx.Account import AccountAPI
from okx.Grid import GridAPI
import pandas as pd
from okx.PublicData import PublicAPI


class OKXExchange:
    """OKX交易所接口类"""
    
    def __init__(self):
        """
        初始化OKX交易所接口
        
        Args:
            api_key: API密钥
            secret_key: 密钥
            passphrase: 密码
            is_sandbox: 是否使用沙盒环境
            is_demo: 是否使用模拟交易
        """
        self.api_key = os.getenv("OKX_API_KEY", "")
        self.secret_key = os.getenv("OKX_SECRET_KEY", "")
        self.passphrase = os.getenv("OKX_PASSPHRASE", "")
        self.flag = os.getenv("FLAG", "0")
        
        self.public = PublicAPI(flag=self.flag)

        # 初始化市场数据接口
        self.market_data = MarketAPI(
            api_key=self.api_key,
            api_secret_key=self.secret_key,
            passphrase=self.passphrase,
            flag=self.flag
        )
        
        # 初始化账户接口
        self.account = AccountAPI(
            api_key=self.api_key,
            api_secret_key=self.secret_key,
            passphrase=self.passphrase,
            flag=self.flag
        )
        
        # 初始化交易接口
        self.trade = TradeAPI(
            api_key=self.api_key,
            api_secret_key=self.secret_key,
            passphrase=self.passphrase,
            debug=True,
            flag=self.flag
        )
        self.grid = GridAPI(
            api_key=self.api_key,
            api_secret_key=self.secret_key,
            passphrase=self.passphrase,
            debug=True,
            flag=self.flag
        )
    
    def get_kline_data(self, 
                      symbol: str, 
                      bar: str = "1m", 
                      limit: int = 100,
                      after: Optional[str] = None,
                      before: Optional[str] = None) -> List[Dict]:
        """
        获取K线数据
        
        Args:
            symbol: 交易对，如 "BTC-USDT"
            bar: K线周期，支持: 1m, 3m, 5m, 15m, 30m, 1H, 2H, 4H, 6H, 12H, 1D, 1W, 1M, 3M, 6M, 1Y
            limit: 返回结果的数量限制，默认100，最大300
            after: 时间戳，返回该时间戳之前的数据
            before: 时间戳，返回该时间戳之后的数据
            
        Returns:
            K线数据列表，每个元素包含: [timestamp, open, high, low, close, volume, currency_volume]
        """
        try:
            # 调用OKX API获取K线数据
            result = self.market_data.get_candlesticks(
                instId=symbol,
                bar=bar,
                limit=str(limit),
                after=after,
                before=before
            )
            
            if result.get('code') == '0':
                data = result.get('data', [])
                return self._parse_kline_data(data)
            else:
                print(f"获取K线数据失败: {result.get('msg', '未知错误')}")
                return []
                
        except Exception as e:
            print(f"获取K线数据异常: {str(e)}")
            return []
    
    
    def _parse_kline_data(self, raw_data: List[List]) -> List[Dict]:
        """
        解析原始K线数据
        
        Args:
            raw_data: 原始数据列表
            
        Returns:
            解析后的K线数据列表
        """
        parsed_data = []
        
        for item in raw_data:
            if len(item) >= 7:
                kline = {
                    'timestamp': int(item[0]),  # 时间戳
                    'open': float(item[1]),     # 开盘价
                    'high': float(item[2]),     # 最高价
                    'low': float(item[3]),      # 最低价
                    'close': float(item[4]),    # 收盘价
                    'volume': float(item[5]),   # 交易量
                    'currency_volume': float(item[6])  # 交易额
                }
                # if int(item[8]) == 1:
                #     parsed_data.append(kline)
                parsed_data.append(kline)
        
        return parsed_data

    def convert_kline_to_dataframe(self, kline_data: List[Dict]) -> pd.DataFrame:
        """
        将K线数据转换为DataFrame格式
        
        Args:
            kline_data: K线数据列表
            
        Returns:
            DataFrame格式的K线数据
        """
        if not kline_data:
            return pd.DataFrame()
        
        # 转换为DataFrame
        df = pd.DataFrame(kline_data)
        
        # 转换时间戳为datetime
        df['datetime'] = pd.to_datetime(df['timestamp'], unit='ms')
        
        # 设置datetime为索引
        df.set_index('datetime', inplace=True)
        
        # 按时间排序
        df.sort_index(inplace=True)
        
        return df


    def get_grid_orders(self, symbol: str = None) -> Dict:
        """
        获取网格订单列表
        
        Args:
            symbol: 交易对符号 (可选)
            
        Returns:
            网格订单列表
        """        
        try:
            result = self.grid.grid_orders_algo_pending(
                algoOrdType='contract_grid',
                instId=symbol if symbol else ''
            )
            
            # 调试：打印原始API响应
            
            if result.get('code') == '0':
                orders = result.get('data', [])
                # 解析和格式化订单数据
                parsed_orders = []
                for order in orders:
                    # 优先使用investment字段作为投资金额，如果没有则使用sz
                    investment_amount = order.get('investment', '')
                    if not investment_amount:
                        investment_amount = order.get('sz', 'N/A')
                    
                    parsed_order = {
                        'instId': order.get('instId', 'N/A'),
                        'algoId': order.get('algoId', 'N/A'),
                        'state': order.get('state', 'N/A'),
                        'gridNum': order.get('gridNum', 'N/A'),
                        'maxPx': order.get('maxPx', 'N/A'),
                        'minPx': order.get('minPx', 'N/A'),
                        'investment': investment_amount,  # 投资金额
                        'sz': order.get('sz', 'N/A'),  # 合约网格使用sz
                        'direction': order.get('direction', 'N/A'),  # 方向
                        'lever': order.get('lever', 'N/A'),  # 杠杆
                        'tdMode': order.get('tdMode', 'N/A'),  # 交易模式
                        'basePos': order.get('basePos', 'N/A'),  # 基础仓位
                        'cTime': order.get('cTime', 'N/A'),  # 创建时间
                        'uTime': order.get('uTime', 'N/A'),  # 更新时间
                        # 新增字段
                        'gridStatus': order.get('gridStatus', 'N/A'),  # 网格状态
                        'tradeNum': order.get('tradeNum', 'N/A'),  # 交易次数
                        'perMaxProfitRate': order.get('perMaxProfitRate', 'N/A'),  # 单次最大收益率
                        'perMinProfitRate': order.get('perMinProfitRate', 'N/A'),  # 单次最小收益率
                        'actualMarginSz': order.get('actualMarginSz', 'N/A'),  # 实际保证金
                        'floatProfit': order.get('floatProfit', 'N/A'),  # 浮动盈亏
                        'totalPnl': order.get('totalPnl', 'N/A')  # 总盈亏
                    }
                    parsed_orders.append(parsed_order)
                
                return {
                    'success': True,
                    'orders': parsed_orders,
                    'count': len(parsed_orders),
                    'raw_response': result  # 保留原始响应用于调试
                }
            else:
                return {
                    'success': False,
                    'error': result.get('msg', 'Unknown error')
                }
                
        except Exception as e:
            return {
                'success': False,
                'error': f'查询网格订单失败: {str(e)}'
                }
    def close_grid_if_exist(self,symbol:str,direction:str):
        orders = self.get_grid_orders(symbol=symbol).get('orders')
        if not orders:
            return
        for order in orders:
            if order.get('direction') == direction:
                result = self.grid.grid_stop_order_algo(algoId=order.get('algoId'),instId=symbol,algoOrdType='contract_grid',stopType='1')
                if result.get('code') == '0':
                    print('关闭网格提交成')
                else:
                    print(f'关闭网格失败:{result}')
    def open_grid_if_not_exist(self,symbol:str,direction:str,amount, atr:float,leverage:int):
        orders = self.get_grid_orders(symbol=symbol).get('orders')
        matching_orders = [order for order in orders if order.get('direction') == direction]
        if not matching_orders:
            ticker_result = self.market_data.get_ticker(instId=symbol)
            price = float(ticker_result['data'][0]['last'])
            maxPx = 0
            minPx = 0
            if direction == 'long':
                minPx = price - 3 * atr
                maxPx = price + 6 * atr
            else:
                minPx = price - 6 * atr
                maxPx = price + 3 * atr
            # 创建网格的逻辑
            slTriggerPx = minPx-100 if direction == 'long' else maxPx+100
            tpTriggerPx = maxPx + 100 if direction == 'long' else minPx- 100
            result = self.grid.grid_order_algo(
                instId=symbol,
                algoOrdType='contract_grid',  # 网格订单类型
                maxPx=str(maxPx),  # 上限价格
                minPx=str(minPx),  # 下限价格
                gridNum=str(20),  # 网格数量
                runType='1',  # 运行类型：1=立即运行
                sz=str(amount),  # 计价币数量（USDT）
                direction=direction,  # 方向
                lever=str(leverage),  # 杠杆
                basePos=True,
                slTriggerPx=str(slTriggerPx),
                tpTriggerPx=str(tpTriggerPx)
            )
            if result.get('code') == '0':
                print('网格创建成功')
            else:
                print(f'网格创建失败: {result}')
    

    def get_positions(self, symbol: Optional[str] = None) -> Dict:
        """
        查询合约持仓
        
        Args:
            symbol: 交易对符号 (可选，如 'BTC-USDT-SWAP')
            
        Returns:
            持仓信息字典
        """
        # 调用OKX API查询持仓
        result = self.account.get_positions(instId=symbol)['data']
        if result:
            return result[0]
        return None
    
    def open_position(self,symbol:str,direction:str,amount:float,leverage:int,slTriggerPx:float):
        position = self.get_positions(symbol=symbol)
        side = 'buy' if direction == 'long' else 'sell'
        position_side = None
        if not position:
            position_side = None
        elif float(position['pos']) < 0:
            position_side = 'short'
        elif float(position['pos']) > 0:
            position_side = 'long'
        self.account.set_leverage(instId=symbol,lever=str(leverage),mgnMode='cross')
        print(f"position_side:{position_side},direction:{direction}")
        if position_side and position_side != direction:
            # 平仓
            close_side = 'sell' if position_side == 'long' else 'buy'
            print(f'准备关闭{position_side}订单,close_side:{close_side}')
            print(f'direction:{direction},position_side:{position_side}')
            res = self.trade.place_order(instId=symbol,tdMode='cross',ordType='market',side=close_side,sz=abs(float(position['pos'])))
            print(f'关闭订单结果:{res}')
            self.trade.cancel_multiple_orders({'instId':symbol})
        elif position_side == direction:
            print(f"更新止损:{slTriggerPx}")
            self.update_stop_price(symbol=symbol,slTriggerPx=slTriggerPx)
            return
        
        ticker_result = self.market_data.get_ticker(instId=symbol)
        current_price = float(ticker_result['data'][0]['last'])
        convert_result = self.public.get_convert_contract_coin(
                            type='1',                    # 币转张
                            instId=symbol,
                            sz=str(amount*leverage),              # USDT数量
                            px=str(current_price),       # 当前价格
                            unit='usds'                  # 币单位
                        )
        contract_count =convert_result.get('data', [])[0].get('sz', '0')
        attachAlgoOrds = {'slTriggerPx':str(slTriggerPx),'slOrdPx':'-1'}                     
        res = self.trade.place_order(instId=symbol,tdMode='cross',side=side,ordType='market',sz=contract_count,attachAlgoOrds=attachAlgoOrds)
        print(res)
    def close_position(self,symbol:str,direction:str):
        position = self.get_positions(symbol=symbol)
        if not position:
            position_side = None
        elif float(position['pos']) < 0:
            position_side = 'short'
        elif float(position['pos']) > 0:
            position_side = 'long'
        if position and position_side == direction:
            # 平仓
            close_side = 'sell' if position_side == 'long' else 'buy'
            print(f'准备关闭{position_side}订单,close_side:{close_side}')
            print(f'direction:{direction},position_side:{position_side}')
            res = self.trade.place_order(instId=symbol,tdMode='cross',ordType='market',side=close_side,sz=abs(float(position['pos'])))
            print(f'关闭订单结果:{res}')
            self.trade.cancel_multiple_orders({'instId':symbol})
    def update_stop_price(self,symbol: str,slTriggerPx:float):
        orders = self.trade.order_algos_list(ordType='conditional',instId=symbol)['data']
        if orders:
            algoId = orders[0]['algoId']
            print(f"准备修改止损:{algoId}")
        else:
            print(f"没有找到 {symbol} 的订单，无法更新止损价。")
            return
        res = self.trade.amend_algo_order(instId=symbol,algoId=algoId,newSlTriggerPx=slTriggerPx,newSlOrdPx='-1',newSlTriggerPxType='mark',newTpTriggerPxType='mark',newTpTriggerPx='0')
        print(res)