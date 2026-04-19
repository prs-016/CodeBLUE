import requests
import io
import pandas as pd

URL = "https://scrippsco2.ucsd.edu/assets/data/atmospheric/stations/in_situ_co2/daily/daily_in_situ_co2_mlo.csv"
response = requests.get(URL)
lines = response.text.splitlines()
data_lines = [l for l in lines if not l.startswith('%') and l.strip()]
print(f"Data lines count: {len(data_lines)}")
raw_df = pd.read_csv(io.StringIO('\n'.join(data_lines)), names=['Yr', 'Mn', 'Dy', 'co2_ppm', 'NB', 'scale', 'sta'], skipinitialspace=True)
print(raw_df.head())
print(raw_df.columns)
