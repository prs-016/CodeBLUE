import requests
import io
import pandas as pd
import numpy as np
URL = "https://scrippsco2.ucsd.edu/assets/data/atmospheric/stations/in_situ_co2/daily/daily_in_situ_co2_mlo.csv"
lines = requests.get(URL).text.splitlines()
data_lines = [l for l in lines if not l.startswith('%') and l.strip()]
raw_df = pd.read_csv(io.StringIO('\n'.join(data_lines)), names=['Yr', 'Mn', 'Dy', 'co2_ppm', 'NB', 'scale', 'sta'], skipinitialspace=True)
df = raw_df.copy()
df["date"] = pd.to_datetime(df[['Yr', 'Mn', 'Dy']].rename(columns={'Yr': 'year', 'Mn': 'month', 'Dy': 'day'}), errors="coerce")
clean = df[["date", "co2_ppm"]].copy()
clean["co2_ppm"] = pd.to_numeric(clean["co2_ppm"], errors="coerce").replace(-99.99, np.nan).ffill()
clean = clean.dropna(subset=["date", "co2_ppm"]).sort_values("date")
print("Clean shape:", clean.shape)
