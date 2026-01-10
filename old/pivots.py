import yfinance as yf
from tests import download_data
import utils


pivotStrength = 2
trendStrength = 3



#if __name__ == "__main__":
symbol = '6EZ25.CME'
start = '2025-07-21'
end = '2025-07-31'
interval = '1h'


data = utils.download_data(symbol, start, end, interval)

pivots = utils.get_pivots(data, pivotStrength, trendStrength)

utils.plot_candles_with_pivots(data, pivots, title=f'Candlestick with Pivots {symbol}')


