from ibapi.client import EClient, Contract
from ibapi.wrapper import EWrapper
from ibapi.order import Order
from ibapi.order_cancel import OrderCancel
from threading import Thread, Event
import time
from datetime import datetime, timedelta
import pandas as pd


class IBClient(EWrapper, EClient):
    
    def __init__(self, host, port, client_id):
        EClient.__init__(self, self)
        self.next_order_id = None
        self.connect(host, port, client_id)
        self.positions_data = []
        self.open_orders_data = []
        self.historical_bars = []
        self.historical_data_received = False

        self.market_depth_data = {}

        self.positions_event = Event()
        self.open_orders_event = Event()

        thread = Thread(target=self.run)
        thread.daemon = True
        thread.start()
    
    def nextValidId(self, orderId):
        super().nextValidId(orderId)
        self.next_order_id = orderId
        print("Next valid order id:", orderId)

    def error(self, req_id, code, msg, misc):
        if code in [2104, 2106, 2158]:
            print(msg)
        else:
            print(f"Error {code}: {msg}")
    
    def position(self, account, contract, position, avgCost):

        if position != 0:
            # Store only positions that are non-zero
            self.positions_data.append((account, contract, position, avgCost))

    def positionEnd(self):
        print("Received all positions.")
        self.positions_event.set()
        # We can proceed to close them here or set a flag to do it later
        # For example, close all positions now:
        #self.close_positions()
    
    def openOrder(self, orderId, contract, order, orderState):
        self.open_orders_data.append((orderId, contract, order, orderState))

    def openOrderEnd(self):
        print("Received all open orders.")
        self.open_orders_event.set()
    
    def get_position_quantiy(self, symbol: str):
        positions = 0
        for (account, contract, posQty, avgCost) in self.positions_data:
            if contract.symbol == symbol:
                positions += posQty
        return positions

    def close_positions(self, symbol=None):
        for (account, contract, posQty, avgCost) in self.positions_data:
            if posQty == 0:
                continue
            if symbol and contract.symbol != symbol:
                continue

            if not getattr(contract, 'exchange', None):
                contract.exchange = "SMART"
            # figure out action
            action = "SELL" if posQty > 0 else "BUY"
            quantity = abs(posQty)
            # create the offsetting market order
            order = Order()
            order.action = action
            order.orderType = "MKT"
            order.totalQuantity = quantity

            # place the order
            print(f"Flattening position: {action} {quantity} of {contract.symbol}/{contract.currency}")
            self.placeOrder(self.next_order_id, contract, order)
            self.next_order_id += 1
    
    def close_open_orders(self, symbol=None):
        for (orderId, contract, order, orderState) in self.open_orders_data:
            if symbol and contract.symbol != symbol:
                continue
            print(f"Cancelling open order ID: {orderId}")
            self.cancelOrder(orderId, OrderCancel())

    def stop(self):
        self.disconnect()
    
    def request_data(self, contract, interval: str):
        if interval == "5min":
            barsize = "5 mins"
            duration = "3 D"
        elif interval == "15min":
            barsize = "15 mins"
            duration = "5 D"
        elif interval == "1h":
            barsize = "1 hour"
            duration = "10 D"
        elif interval == "4h":
            barsize = "4 hours"
            duration = "40 D"
        elif interval == "1min":
            barsize = "1 min"
            duration = "1 D"
        self.reqHistoricalData(
            reqId=1,
            contract=contract,
            endDateTime="",         # Now
            durationStr=duration,      # 1 day of data
            barSizeSetting=barsize,
            whatToShow="MIDPOINT",
            useRTH=0,               # 0 = all trading hours
            formatDate=1,
            keepUpToDate=False,
            chartOptions=[]
        )
    
    def historicalData(self, reqId, bar):
        #print(f"[historicalData] ReqID={reqId} | Time={bar.date}, O={bar.open}, H={bar.high}, L={bar.low}, C={bar.close}")
        self.historical_bars.append({
            'date': bar.date.split(" US/Eastern")[0],
            'Open': bar.open,
            'High': bar.high,
            'Low': bar.low,
            'Close': bar.close
        })
    
    def historicalDataEnd(self, reqId, start, end):

        print(f"[historicalDataEnd] ReqID={reqId} from {start} to {end}")
        print("Initial historical download complete.")
        self.historical_data_received = True
    
    def create_dataframe(self):
        if not self.historical_bars:
            return pd.DataFrame(columns=["Open", "High", "Low", "Close"])

        df = pd.DataFrame(self.historical_bars)
        df['date'] = pd.to_datetime(df['date'])
        df.sort_values('date', inplace=True)
        df.set_index('date', inplace=True)
        df = df[~df.index.duplicated(keep='last')]
        #print(df.index)

        return df
    
    def request_mkt_depth(self, contract, num_rows=10):
        """
        Request market depth for the given contract.
        num_rows determines how many levels of depth to retrieve.
        """
        # Typically, for forex, you'd use the 'IDEALPRO' exchange, but IB may also
        # use 'SMART' for some pairs. Be sure your contract details are correct.
        self.market_depth_data.clear()
        self.reqMktDepth(
            reqId=1002,              # an arbitrary ID - just ensure it's unique
            contract=contract,
            numRows=num_rows,
            isSmartDepth=False,      # set True if you'd like to get SMART-routed depth
            mktDepthOptions=[]
        )
        print(f"Requested Market Depth for {contract.symbol}/{contract.currency}")
    
    def updateMktDepth(self, reqId: int, position: int, operation: int, side: int,
                       price: float, size: float):
        """
        Called when TWS receives Level I depth updates.
        
        operation: 0 = insert, 1 = update, 2 = delete
        side: 0 = bid, 1 = ask
        position: which level (0 = best bid/ask)
        """
        if reqId not in self.market_depth_data:
            self.market_depth_data[reqId] = []

        # Simplify operation and side to strings:
        op_str = {0: "insert", 1: "update", 2: "delete"}.get(operation, "unknown")
        side_str = {0: "bid", 1: "ask"}.get(side, "unknown")

        # We'll store each update as a dict. You could also store in a DataFrame.
        update_entry = {
            "position": position,
            "operation": op_str,
            "side": side_str,
            "price": price,
            "size": size
        }

        # Store or update the record
        self.market_depth_data[reqId].append(update_entry)

        # Here, we simply print the update, but you can handle it more elaborately:
        print(f"[updateMktDepth] reqId={reqId} pos={position} side={side_str} "
              f"op={op_str} price={price} size={size}")

    def updateMktDepthL2(self, reqId: int, position: int, marketMaker: str,
                         operation: int, side: int, price: float, size: float,
                         isSmartDepth: bool):
        """
        Called when TWS receives Level II depth updates.
        
        Similar parameters to updateMktDepth, but includes the market maker ID.
        """
        if reqId not in self.market_depth_data:
            self.market_depth_data[reqId] = []

        op_str = {0: "insert", 1: "update", 2: "delete"}.get(operation, "unknown")
        side_str = {0: "bid", 1: "ask"}.get(side, "unknown")

        update_entry = {
            "position": position,
            "marketMaker": marketMaker,
            "operation": op_str,
            "side": side_str,
            "price": price,
            "size": size,
            "isSmartDepth": isSmartDepth
        }

        self.market_depth_data[reqId].append(update_entry)

        # Print the update (or handle it as needed):
        print(f"[updateMktDepthL2] reqId={reqId} pos={position} mm={marketMaker} "
              f"side={side_str} op={op_str} price={price} size={size} smart={isSmartDepth}")



def create_contract(currency_pair: str, type: str, exchange: str):
    contract = Contract()
    contract.secType = type
    contract.exchange = exchange
    contract.symbol = currency_pair.split("/")[0]
    contract.currency = currency_pair.split("/")[1]
    return contract

def get_data(currency_pair: str, interval: str):
    client = IBClient("127.0.0.1", 7497, 1)
    
    while client.next_order_id is None:
        time.sleep(0.1)
    
    contract = create_contract(currency_pair, "CASH", "IDEALPRO")
    client.request_data(contract, interval)
    while not client.historical_data_received:
        time.sleep(0.1)
  
    df = client.create_dataframe()
    client.disconnect()
    return df

def create_bracket_order(parent_order_id: int,
                       action: str,
                       quantity: float,
                       entry_order_type: str,
                       entry_price: float,
                       stop_price: float,
                       take_profit_price: float,
                       trailing_pips: float = None,
                       pip_size: float = 0.0001,
                       tif: str = None,
                       good_till_date: str = None):

    # parent order
    parent = Order()
    parent.orderId = parent_order_id
    parent.action = action
    parent.orderType = entry_order_type
    parent.totalQuantity = quantity
    if entry_order_type == "LMT":
        parent.lmtPrice = entry_price
    elif entry_order_type == "STP":
        parent.auxPrice = entry_price

    if tif:
        parent.tif = tif 
    if good_till_date:
        parent.goodTillDate = good_till_date
    parent.transmit = False

    # stop loss
    stop_loss = Order()
    stop_loss.orderId = parent_order_id + 1
    stop_loss.action = "BUY" if action == "SELL" else "SELL"
    if trailing_pips is not None:
        stop_loss.orderType = "TRAIL"
        stop_loss.trailingPercent = 100 * trailing_pips * pip_size / entry_price
    else:
        stop_loss.orderType = "STP"
        stop_loss.auxPrice = stop_price 
    stop_loss.totalQuantity = quantity
    stop_loss.parentId = parent_order_id
    stop_loss.transmit = False  

    # take profit
    take_profit = Order()
    take_profit.orderId = parent_order_id + 2
    take_profit.action = "BUY" if action == "SELL" else "SELL"
    take_profit.orderType = "LMT"
    take_profit.lmtPrice = take_profit_price
    take_profit.totalQuantity = quantity
    take_profit.parentId = parent_order_id
    take_profit.transmit = True

    # group stop loss and take profit
    oca_group = f"OCA_{parent_order_id}"
    stop_loss.ocaGroup = oca_group
    take_profit.ocaGroup = oca_group
    # 3 = All remaining orders in the group are canceled when one order fills.
    stop_loss.ocaType = 3
    take_profit.ocaType = 3

    return [parent, stop_loss, take_profit]

def execute_order(client: IBClient, currency_pair: str, action, entry_order_type, entry_price, stop_price, take_profit_price, trailing_pips = None, pip_size = 0.0001, quantity = 100000):

    expiration_datetime = datetime.utcnow() + timedelta(minutes=45)
    gtd_str = expiration_datetime.strftime("%Y%m%d-%H:%M:%S")

    contract = create_contract(currency_pair, type="CFD", exchange="SMART")

    bracket = create_bracket_order(
        parent_order_id=client.next_order_id,
        action=action,
        quantity=quantity,
        entry_order_type=entry_order_type,
        entry_price=entry_price,
        stop_price=stop_price,
        take_profit_price=take_profit_price,
        trailing_pips=trailing_pips,
        pip_size=pip_size,
        tif="GTD",
        good_till_date=gtd_str
    )

    for order in bracket:
        client.placeOrder(order.orderId, contract, order)

    print(
        f"Placed bracket order:\n"
        f"  Main (LMT)    ID={bracket[0].orderId}, Price={bracket[0].lmtPrice}\n"
        f"  Stop (STP)    ID={bracket[1].orderId}, Stop={bracket[1].auxPrice}\n"
        f"  Target (LMT)  ID={bracket[2].orderId}, Price={bracket[2].lmtPrice}"
    )
    
    time.sleep(1)


def close_all(symbol=None):
    client = IBClient("127.0.0.1", 7497, 1)

    # Wait until next_valid_order_id is received.
    while client.next_order_id is None:
        time.sleep(0.2)
    
    # Request positions and open orders.
    client.reqPositions()
    client.reqAllOpenOrders()

    # Wait for the positions and open orders callbacks to finish.
    print("Waiting for positions data...")
    client.positions_event.wait(timeout=10)  # Adjust timeout as needed.
    print("Waiting for open orders data...")
    client.open_orders_event.wait(timeout=10)

    client.close_open_orders(symbol)
    client.close_positions(symbol)

    time.sleep(2)
    client.disconnect()


if __name__ == "__main__":
    client = IBClient("127.0.0.1", 7497, 1)
    while client.next_order_id is None:
        time.sleep(0.2)
    
    client.reqPositions()
    client.positions_event.wait(timeout=10)
    positions = client.get_position_quantiy("EUR")
    print(positions)
    client.disconnect()
