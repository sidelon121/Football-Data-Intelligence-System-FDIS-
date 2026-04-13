import pandas as pd

# 1. Load Data
df = pd.read_csv('dummy_matches.csv')

# 2. Kalkulasi Sederhana: Akurasi Tembakan (Shot on Target / Total Shots)
df['home_accuracy'] = (df['home_sot'] / df['home_shots']) * 100

print("--- Hasil Analisis Cepat FDIS ---")
print(df[['home_team', 'home_accuracy']])

# 3. Temukan tim paling efisien
top_team = df.loc[df['home_accuracy'].idxmax()]
print(f"\nTim paling akurat: {top_team['home_team']} ({top_team['home_accuracy']:.2f}%)")