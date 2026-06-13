import pandas as pd
import numpy as np
import logging

# Configure basic logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger("Forecaster")

# Attempt importing prophet, fall back gracefully if missing
try:
    from prophet import Prophet
    HAS_PROPHET = True
except ImportError:
    HAS_PROPHET = False
    logger.warning("Prophet package is not installed. All forecasts will fall back to linear trend.")

# Constants
MIN_DATAPOINTS_REQUIRED = 5
FORECAST_HORIZON_YEARS = 1
CONFIDENCE_INTERVAL = 0.80

def prepare_yearly_series_from_df(df_track_b, skill):
    """Filter by skill and aggregate demand count by posted_year."""
    sub = df_track_b[df_track_b['skill'] == skill]
    yearly = sub.groupby('posted_year').size().reset_index(name='y')
    yearly.columns = ['year', 'y']
    return yearly

def fit_prophet_yearly(yearly_df):
    """Fit a basic Prophet model on yearly frequency data and predict 1 year forward."""
    df = yearly_df.rename(columns={'year': 'ds_year'})
    df['ds'] = pd.to_datetime(df['ds_year'], format='%Y')
    
    # Disable standard seasonalities because data points are yearly (only 1 point/year)
    m = Prophet(yearly_seasonality=False,
                weekly_seasonality=False,
                daily_seasonality=False,
                interval_width=CONFIDENCE_INTERVAL)
    m.fit(df[['ds', 'y']])
    
    future = m.make_future_dataframe(periods=FORECAST_HORIZON_YEARS, freq='YS')
    forecast = m.predict(future)
    forecast['yhat'] = forecast['yhat'].clip(lower=0)
    forecast['yhat_lower'] = forecast['yhat_lower'].clip(lower=0)
    return forecast[['ds', 'yhat', 'yhat_lower', 'yhat_upper']]

def fit_linear_trend(yearly_df):
    """Calculate simple linear trend using numpy polyfit."""
    x = yearly_df['year'].values
    y = yearly_df['y'].values
    slope, intercept = np.polyfit(x, y, 1)
    next_year = x.max() + FORECAST_HORIZON_YEARS
    forecast_y = max(0, slope * next_year + intercept)
    return next_year, forecast_y, slope

def get_trend_direction(historical_yearly, forecast_value):
    """Determine directional indicator based on percent change from last actual."""
    if len(historical_yearly) == 0:
        return "Stable ->"
    last_actual = historical_yearly['y'].iloc[-1]
    delta_pct = (forecast_value - last_actual) / max(last_actual, 1) * 100
    if delta_pct > 10:  return "Rising ^"
    if delta_pct < -10: return "Declining v"
    return "Stable ->"

def forecast_skill(df_track_b, skill):
    """Compute forecast for a given skill using Prophet, falling back to linear if required."""
    yearly = prepare_yearly_series_from_df(df_track_b, skill)
    if len(yearly) < MIN_DATAPOINTS_REQUIRED:
        logger.info(f"Skipping '{skill}': insufficient data points ({len(yearly)} < {MIN_DATAPOINTS_REQUIRED}).")
        return None

    # Fallback to linear directly if prophet is not available
    if not HAS_PROPHET:
        next_year, forecast_y, slope = fit_linear_trend(yearly)
        return {
            "skill": skill,
            "method": "linear_trend",
            "forecast_year": next_year,
            "forecast_value": round(forecast_y, 1),
            "note": "Prophet not installed — linear trend fallback used"
        }

    prophet_result = fit_prophet_yearly(yearly)
    ci_width = (prophet_result['yhat_upper'] - prophet_result['yhat_lower']).iloc[-1]
    pred_val = prophet_result['yhat'].iloc[-1]

    if ci_width > pred_val * 1.5:
        next_year, forecast_y, slope = fit_linear_trend(yearly)
        logger.info(f"Skill '{skill}' fell back to linear trend (Prophet confidence interval too wide: {ci_width:.2f} > {pred_val * 1.5:.2f}).")
        return {
            "skill": skill,
            "method": "linear_trend",
            "forecast_year": next_year,
            "forecast_value": round(forecast_y, 1),
            "note": "Prophet CI too wide — linear trend used instead"
        }
    else:
        logger.info(f"Skill '{skill}' forecasted successfully using Prophet.")
        return {
            "skill": skill,
            "method": "prophet",
            "forecast_year": 2027,
            "forecast_value": round(pred_val, 1),
            "ci_lower": round(prophet_result['yhat_lower'].iloc[-1], 1),
            "ci_upper": round(prophet_result['yhat_upper'].iloc[-1], 1)
        }

def run_top_skills_forecasts(df_long):
    """Compute forecasts for the top 10 skills by count in the dataset."""
    df_track_b = df_long[df_long['posted_year'] != 'Not Specified'].copy()
    df_track_b['posted_year'] = df_track_b['posted_year'].astype(int)

    top_skills = df_long['skill'].value_counts().head(10).index.tolist()
    logger.info(f"Beginning forecasts for top 10 skills: {top_skills}")

    results = []
    for skill in top_skills:
        res = forecast_skill(df_track_b, skill)
        if res is not None:
            yearly = prepare_yearly_series_from_df(df_track_b, skill)
            res['direction'] = get_trend_direction(yearly, res['forecast_value'])
            results.append(res)
    
    return pd.DataFrame(results)

if __name__ == '__main__':
    # Test script execution when run stand-alone
    import os
    data_path = 'data/clean/primary_skills_long.csv'
    if os.path.exists(data_path):
        df_long_test = pd.read_csv(data_path)
        forecasts_df = run_top_skills_forecasts(df_long_test)
        print("\n=== Forecast Summary Table ===")
        print(forecasts_df.to_string(index=False))
