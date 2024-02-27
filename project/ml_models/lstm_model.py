from ml_models.lstm_model import StockPricePredictionModel
from data_provider.data_provider import DataProvider

data_provider = DataProvider(api_key="your_api_key")
prediction_model = StockPricePredictionModel()

real_time_data = data_provider.fetch_real_time_data(symbol="AAPL")


prediction = prediction_model.predict(real_time_data)
