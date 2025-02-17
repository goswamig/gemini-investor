from gemini_investor.alpaca_utils import TradingClientSingleton, create_option_ticker, submit_market_order, create_option_ticker
from alpaca.trading.requests import OrderSide, TimeInForce, GetOptionContractsRequest, AssetStatus
from gemini_investor.alpaca_utils import submit_limit_buy_order, submit_limit_sell_order, submit_sell_market_order, submit_buy_market_order
from gemini_investor.common import now


"""
This module exclusively handles option contracts for stocks. 
These functions are not designed to work with stocks directly.
"""


def get_option_contract(
        underlying_symbol: str, 
        option_type: str, 
        expiration_date: str = None, 
        strike_price: float = None, 
        min_open_interest: int = 0):
    """
    Fetches an information option contract matching the given criteria.

    Args:
        underlying_symbol (str): The underlying stock symbol (e.g., AAPL).
        option_type (str): "C" for call, "P" for put.
        expiration_date (str, optional): Expiration date in YYYY-MM-DD format. If None, fetches the nearest expiration.
        strike_price (float, optional): Strike price. If None, fetches the closest to the current underlying price.
        min_open_interest (int, optional): Minimum open interest for the contract.

    Returns:
        alpaca.data.models.OptionContract or None: The matching option contract or None if not found.
    """
    min_open_interest = int(min_open_interest)

    if option_type.lower() == 'c':
        option_type = 'call'
    elif option_type.lower() == 'p':
        option_type = 'put'
    req = GetOptionContractsRequest(
        underlying_symbols=[underlying_symbol],
        status=AssetStatus.ACTIVE,
        type=option_type.lower(),  # Use lowercase for Alpaca
        expiration_date_gte=now().date() if not expiration_date else expiration_date,
        limit=100,  # Fetch enough to find a good match
    )
    contracts = TradingClientSingleton.get_instance().get_option_contracts(req).option_contracts

    matching_contracts = [c for c in contracts if c.open_interest and int(c.open_interest) >= min_open_interest]

    if expiration_date:
        matching_contracts = [c for c in matching_contracts if c.expiration_date == expiration_date]

    if strike_price:
        matching_contracts = sorted(matching_contracts, key=lambda c: abs(c.strike_price - strike_price))

    return str(matching_contracts[0]) if matching_contracts else None


def buy_option_by_market_price(
        underlying_symbol: str,
        expiration_date: str,
        option_type: str,
        strike_price: float,
        qty: int):
    """Buy an option at market price, retuns the order id.

    Args:
        underlying_symbol: The underlying symbol of the option.
        expiration_date: The expiration date of the option.
        option_type: The type of the option. Should be 'C' (Call) or 'P' (Put).
        strike_price: The strike price of the option.
        qty: The quantity of the option to buy. Mush be a positive integer. You MUST provide it, even if qty is 1.
    """
    strike_price = float(strike_price)
    qty = int(qty)
    option_ticker = create_option_ticker(
        underlying_symbol=underlying_symbol,
        expiration_date=expiration_date,
        option_type=option_type,
        strike_price=strike_price,
    )
    return submit_market_order(option_ticker, qty, time_in_force=TimeInForce.DAY, side=OrderSide.BUY)


def sell_option_by_market_price_with_option_ticker(
        option_ticker: str, qty: int):
    """
    Sells an option contract at the market price, using the option ticker.

    Args:
        option_ticker (str): The option contract ticker.
        qty (int): Quantity of the option contract to sell.
    """
    return submit_sell_market_order(option_ticker, qty)


def sell_option_by_market_price(
        underlying_symbol: str, 
        expiration_date: str, 
        option_type: str, 
        strike_price: float, 
        qty: int):
    """
    Sells an option contract at the market price, using a ticker from the underlying asset.

    Args:
        underlying_symbol (str): The underlying stock symbol (e.g., AAPL).
        expiration_date (str): Expiration date in YYYY-MM-DD format.
        option_type (str): "C" for call, "P" for put.
        strike_price (float): Strike price.
        qty (int): Quantity of the option contract to sell.
    """
    symbol = create_option_ticker(underlying_symbol, expiration_date, option_type, strike_price)
    return sell_option_by_market_price_with_option_ticker(symbol, qty)


def sell_option_by_limit_price(
        option_ticker: str, 
        qty: int, 
        limit_price: float):
    """
    Sets the upper profit limit of the exit strategy from the existing option contract.
    Cannot be used for Stop-Loss exit strategy.

    Args:
        option_ticker (str): The option contract ticker.
        qty (int): Quantity of the option contract to sell.
        limit_price (float): The limit price at which to sell the option contract.
    """
    qty = int(qty)
    limit_price = float(limit_price)
    return submit_limit_sell_order(option_ticker, qty, limit_price, time_in_force=TimeInForce.DAY)
