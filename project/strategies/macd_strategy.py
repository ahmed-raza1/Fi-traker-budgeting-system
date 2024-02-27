 def __init__(self, short_window, long_window):
        self.short_window = short_window
        self.long_window = long_window

    def evaluate(self, price_data):
        close_prices = price_data.close
        short_ma = close_prices.rolling(window=self.short_window).mean()
        long_ma = close_prices.rolling(window=self.long_window).mean()

        if short_ma[-1] > long_ma[-1] and short_ma[-2] <= long_ma[-2]:
            return "Buy"
        elif short_ma[-1] < long_ma[-1] and short_ma[-2] >= long_ma[-2]:
            return "Sell"
        else:
            return "Hold"
