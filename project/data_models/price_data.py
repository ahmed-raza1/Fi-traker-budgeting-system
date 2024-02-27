class PriceData:
    def __init__(self, symbol, date, open_price, high, low, close, volume):
        self._symbol = symbol
        self._date = date
        self._open_price = open_price
        self._high = high
        self._low = low
        self._close = close
        self._volume = volume

    # Getters
    @property
    def symbol(self):
        return self._symbol

    @property
    def date(self):
        return self._date

    @property
    def open_price(self):
        return self._open_price

    @property
    def high(self):
        return self._high

    @property
    def low(self):
        return self._low

    @property
    def close(self):
        return self._close

    @property
    def volume(self):
        return self._volume

    # Setters
    @symbol.setter
    def symbol(self, value):
        self._symbol = value

    @date.setter
    def date(self, value):
        self._date = value

    @open_price.setter
    def open_price(self, value):
        self._open_price = value

    @high.setter
    def high(self, value):
        self._high = value

    @low.setter
    def low(self, value):
        self._low = value

    @close.setter
    def close(self, value):
        self._close = value

    @volume.setter
    def volume(self, value):
        self._volume = value
