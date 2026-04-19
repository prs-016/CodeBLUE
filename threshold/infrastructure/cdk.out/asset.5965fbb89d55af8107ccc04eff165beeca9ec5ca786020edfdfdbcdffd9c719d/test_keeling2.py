import requests
import io
import pandas as pd
import numpy as np

def transform(df: pd.DataFrame) -> pd.DataFrame:
    if 'date' not in df.columns and all(c in df.columns for c in ['Yr', 'Mn', 'Dy']):
        df["date"] = pd.to_datetime(df[['Yr', 'Mn', 'Dy']].rename(columns={'Yr': 'year', 'Mn': 'month', 'Dy': 'day'}), errors="coerce")
    elif 'date' not in df.columns:
        date_col = next((col for col in df.columns if "date" in col.lower()), df.columns[0])
        df = df.rename(columns={date_col: "date"})
    
    co2_col = "co2_ppm" if "co2_ppm" in df.columns else next((col for col in df.columns if "co2" in col.lower()), df.columns[-1])
    clean = df[["date", co2_col]].rename(columns={co2_col: "co2_ppm"}).copy()
    clean["co2_ppm"] = pd.to_numeric(clean["co2_ppm"], errors="coerce").replace(-99.99, np.nan).ffill()
    clean = clean.dropna(subset=["date", "co2_ppm"]).sort_values("date")
    clean["co2_trend"] = clean["co2_ppm"].rolling(30, min_periods=1).mean()
    clean["yoy_change"] = clean["co2_ppm"].pct_change(365).replace([np.inf, -np.inf], np.nan).fillna(0.0)
    rate_this_year = clean["co2_ppm"].diff(365)
    rate_last_year = rate_this_year.shift(365).replace(0, np.nan)
    clean["acceleration"] = ((rate_this_year - rate_last_year) / rate_last_year).replace([np.inf, -np.inf], np.nan).fillna(0.0)
    clean["date"] = clean["date"].dt.strftime("%Y-%m-%d")
    return clean.round(6)

URL = "https://scrippsco2.ucsd.edu/assets/data/atmospheric/stations/in_situ_co2/daily/daily_in_situ_co2_mlo.csv"
response = requests.get(URL)
lines = response.text.splitlines()
data_lines = [l for l in lines if not l.startswith('%') and l.strip()]
raw_df = pd.read_csv(io.StringIO('\n'.join(data_lines)), names=['Yr', 'Mn', 'Dy', 'co2_ppm', 'NB', 'scale', 'sta'], skipinitialspace=True)
try:
    final_df = transform(raw_df)
    print("Success")
except Exception as e:
    import traceback
    traceback.print_exc()

