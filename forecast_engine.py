import pandas as pd
from prophet import Prophet


def forecast_product_demand(product_df, forecast_days=30):
    """
    Takes historical data for one product and forecasts future daily demand.
    Prophet expects:
    - ds = date column
    - y = target column
    """
    df = product_df.copy()

    prophet_df = df[["date", "units_sold"]].rename(
        columns={"date": "ds", "units_sold": "y"}
    )

    prophet_df["ds"] = pd.to_datetime(prophet_df["ds"])
    prophet_df = prophet_df.sort_values("ds")

    model = Prophet(
        daily_seasonality=False,
        weekly_seasonality=True,
        yearly_seasonality=True
    )

    model.fit(prophet_df)

    future = model.make_future_dataframe(periods=forecast_days)
    forecast = model.predict(future)

    future_only = forecast.tail(forecast_days)[["ds", "yhat", "yhat_lower", "yhat_upper"]]

    future_only["yhat"] = future_only["yhat"].clip(lower=0)
    future_only["yhat_lower"] = future_only["yhat_lower"].clip(lower=0)
    future_only["yhat_upper"] = future_only["yhat_upper"].clip(lower=0)

    total_forecast = future_only["yhat"].sum()

    return model, future_only, total_forecast
