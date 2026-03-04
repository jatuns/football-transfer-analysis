import pandas as pd

df = pd.read_csv("players_data-2024_2025.csv")

print(f"Satır sayısı: {df.shape[0]}")
print(f"Kolon sayısı: {df.shape[1]}")
print("\nİlk 5 satır:")
print(df.head())
print("\nKolon isimleri:")
print(df.columns.tolist())

print("\nLigler:")
print(df['Comp'].value_counts())

print("\nPozisyonlar:")
print(df['Pos'].value_counts())

print("\nEksik veri oranı (ilk 10 kolon):")
print(df.isnull().sum().head(10))

# Tekrar eden kolonları filtrele
tekrar_kolonlar = [col for col in df.columns if any(
    col.startswith(prefix) for prefix in [
        'Rk_stats_', 'Nation_stats_', 'Age_stats_', 
        'Pos_stats_', 'Comp_stats_', 'Born_stats_'
    ]
)]

print(f"Atılacak tekrar kolon sayısı: {len(tekrar_kolonlar)}")

df_clean = df.drop(columns=tekrar_kolonlar)
print(f"Kalan kolon sayısı: {df_clean.shape[1]}")
print(df_clean.columns.tolist())

# Kalecileri ayır
gk = df_clean[df_clean['Pos'] == 'GK']
outfield = df_clean[df_clean['Pos'] != 'GK']

print(f"Kaleci sayısı: {gk.shape[0]}")
print(f"Saha oyuncusu sayısı: {outfield.shape[0]}")

# Kaleci kolonları
kaleci_kolonlar = ['Player', 'Squad', 'Comp', 'Age', 'MP', 'Min', 
                   'GA', 'GA90', 'SoTA', 'Saves', 'Save%', 
                   'CS', 'CS%', 'PKsv', 'PSxG', 'PSxG+/-']

print("\nKaleci verisi örnek:")
print(gk[kaleci_kolonlar].head())

# Ligleri listele
ligler = df_clean[['Comp']].drop_duplicates()
print("Ligler:")
print(ligler)

# Kulüpleri listele  
kulupler = df_clean[['Squad', 'Comp']].drop_duplicates()
print(f"\nToplam kulüp sayısı: {kulupler.shape[0]}")
print(kulupler.head(10))