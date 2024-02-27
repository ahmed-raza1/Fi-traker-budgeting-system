 def __init__(self, period, overbought_threshold=70, oversold_threshold=30):
        self.period = period
        self.overbought_threshold = overbought_threshold
        self.oversold_threshold = oversold_threshold

    def evaluate(self, price_data):
        close_prices = price_data.close
        price_diff = close_prices.diff()
        avg_gain = price_diff[price_diff > 0].rolling(window=self.period).mean()
        avg_loss = -price_diff[price_diff < 0].rolling(window=self.period).mean()
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))

        if rsi[-1] > self.overbought_threshold:
            return "Sell"
        elif rsi[-1] < self.oversold_threshold:
            return "Buy"
        else:
            return "Hold"
