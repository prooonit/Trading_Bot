import time
import hmac
import hashlib
import requests
import logging
from urllib.parse import urlencode


logger = logging.getLogger("TradingBot")
logger.setLevel(logging.DEBUG)


console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)


file_handler = logging.FileHandler("bot.log")
file_handler.setLevel(logging.DEBUG)

formatter = logging.Formatter("[%(asctime)s] %(levelname)s: %(message)s")
console_handler.setFormatter(formatter)
file_handler.setFormatter(formatter)

logger.addHandler(console_handler)
logger.addHandler(file_handler)



class BinanceClient:
    BASE_URL = "https://testnet.binancefuture.com"

    def __init__(self, api_key, api_secret):
        self.api_key = api_key
        self.api_secret = api_secret

        self.session = requests.Session()
        self.session.headers.update({"X-MBX-APIKEY": api_key})

    def _timestamp(self):
        return int(time.time() * 1000)

    def _sign(self, params):
        query = urlencode(params)
        return hmac.new(
            self.api_secret.encode(),
            query.encode(),
            hashlib.sha256
        ).hexdigest()

    def request(self, method, path, params=None, signed=False):
        if params is None:
            params = {}

        if signed:
            params["timestamp"] = self._timestamp()
            params["recvWindow"] = 5000
            params["signature"] = self._sign(params)

        url = self.BASE_URL + path
        logger.debug(f"REQUEST {method} {url} PARAMS={params}")

        try:
            if method == "GET":
                response = self.session.get(url, params=params)
            else:
                response = self.session.post(url, data=params)

        except requests.exceptions.RequestException as e:
            logger.error(f"Network Error: {e}")
            return None

        try:
            data = response.json()
        except ValueError:
            logger.error(f"Invalid JSON Response: {response.text}")
            return None

        logger.debug(f"RESPONSE: {data}")
        return data

  

    def market_order(self, symbol, side, qty):
        params = {
            "symbol": symbol,
            "side": side,
            "type": "MARKET",
            "quantity": qty
        }
        return self.request("POST", "/fapi/v1/order", params, signed=True)

    def limit_order(self, symbol, side, qty, price):
        params = {
            "symbol": symbol,
            "side": side,
            "type": "LIMIT",
            "timeInForce": "GTC",
            "quantity": qty,
            "price": price
        }
        return self.request("POST", "/fapi/v1/order", params, signed=True)



def validate_symbol(symbol):
    valid = symbol.isalnum() and symbol.endswith("USDT")
    if not valid:
        logger.error("Invalid Symbol! Example: BTCUSDT")
    return valid


def validate_quantity(qty):
    try:
        qty = float(qty)
        return qty > 0
    except:
        logger.error("Quantity must be a number!")
        return False


def validate_price(price):
    try:
        price = float(price)
        return price > 0
    except:
        logger.error("Price must be numeric!")
        return False


def cli_menu(client):
    while True:
        print("\n=== Binance Testnet Trading Bot ===")
        print("1. Market Order")
        print("2. Limit Order")
        print("3. Exit")
        choice = input("Select: ").strip()

        if choice == "1":
            symbol = input("Symbol (e.g., BTCUSDT): ").upper()

            if not validate_symbol(symbol):
                continue

            side = input("Side (BUY/SELL): ").upper()
            if side not in ("BUY", "SELL"):
                logger.error("Invalid side!")
                continue

            qty = input("Quantity: ")
            if not validate_quantity(qty):
                continue

            result = client.market_order(symbol, side, float(qty))
            logger.info(f"Market Order Result: {result}")

        elif choice == "2":
            symbol = input("Symbol (e.g., BTCUSDT): ").upper()
            if not validate_symbol(symbol):
                continue

            side = input("Side (BUY/SELL): ").upper()
            if side not in ("BUY", "SELL"):
                logger.error("Invalid side!")
                continue

            qty = input("Quantity: ")
            if not validate_quantity(qty):
                continue

            price = input("Limit Price: ")
            if not validate_price(price):
                continue

            result = client.limit_order(symbol, side, float(qty), float(price))
            logger.info(f"Limit Order Result: {result}")

        elif choice == "3":
            logger.info("Exiting bot.")
            break

        else:
            logger.error("Invalid option! Try again.")



if __name__ == "__main__":
    print("=== Binance Futures Testnet Bot ===")
    api_key = input("Enter API Key: ").strip()
    api_secret = input("Enter API Secret: ").strip()

    bot = BinanceClient(api_key, api_secret)
    cli_menu(bot)
