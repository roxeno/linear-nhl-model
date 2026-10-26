from pathlib import Path 

import pandas as pd
import numpy as np

#skaters season

df_2022_skater = pd.read_csv("../datasets/raw_data/skaters_2022.csv")
df_2023_skater = pd.read_csv("../datasets/raw_data/skaters_2023.csv")
df_2024_skater = pd.read_csv("../datasets/raw_data/skaters_2024.csv")


RAW_DIR = Path("../datasets/raw_data")
OUTPUT_FILE = Path("../datasets/trimmed_skaters/career_hd_priors.csv")

def trim_careerdefenders():
    df = df_2023_skater
    df = df[df['situation'] == 'all']
    
    # Build the team defense metric
    df = df.groupby('team').agg(
            total_icetime=('icetime', 'sum'),
            total_xga=('OnIce_A_xGoals', 'sum')
        ).reset_index()

    df['Career_team_xGA_per_60'] = df['total_xga'] / (df['total_icetime'] / 3600)
    df = df[['team', 'Career_team_xGA_per_60']]

    df.to_csv("../datasets/raw_data/defenders/C_Defender_hockeyskater.csv", index=False, encoding="utf-8")

def trim_skater_season():
    df = df_2024_skater

    final_destination_skater = "../datasets/raw_data/skaters"
    final_destination_defender = "../datasets/raw_data/defenders"
    
    # FIX 2: Filter to 'all' situations so we don't double-count events
    df_all = df[df['situation'] == 'all']

    # Build the team defense metric
    df_def = df_all.groupby('team').agg(
        total_icetime=('icetime', 'sum'),
        total_xga=('OnIce_A_xGoals', 'sum')
    ).reset_index()
    
    df_def['team_xGA_per_60'] = df_def['total_xga'] / (df_def['total_icetime'] / 3600)

    league_avg = df_def["team_xGA_per_60"].mean()
    df_def["leagueAvgXGAper60"] = league_avg
    # Save both files
    df.to_csv(final_destination_skater, index=False, encoding="utf-8")
    
    # Just save the 3 clean columns for the analyzer
    df_def = df_def[['team', 'team_xGA_per_60','leagueAvgXGAper60']]
    df_def.to_csv(final_destination_defender, index=False, encoding="utf-8")

    print("Download complete")

def build_career_data():
    # 1. Find all raw files (adjust the pattern to match your filenames)
    # Assuming you downloaded: skaters_2023.csv, skaters_2024.csv, skaters_2025.csv
    files = list(RAW_DIR.glob("skaters_*.csv"))
    
    if not files:
        print("❌ No raw files found in data/raw/ matching 'skaters_*.csv'")
        return

    print(f"Found {len(files)} files. Stacking...")
    
    all_dfs = []
    for f in files:
        print(f"  -> Loading {f.name}")
        df = pd.read_csv(f)
        
        # Filter to only 'all' situations (to avoid double counting)
        df = df[df['situation'] == 'all']
        
        # Keep ONLY the columns we need for career priors to save memory
        cols_to_keep = ['playerId', 'name', 'games_played','I_F_highDangerShots', 'I_F_shotsOnGoal', 'icetime']
        
        # Safety check: if your older files don't have HD shots, default to 0
        if 'I_F_highDangerShots' not in df.columns:
            df['I_F_highDangerShots'] = 0
            
        all_dfs.append(df[cols_to_keep])

    # 2. Combine them all into one massive dataframe
    master_df = pd.concat(all_dfs, ignore_index=True)
    print(f"Total combined rows: {len(master_df)}")

    # 3. Group by player and SUM their entire career
    print("Calculating career totals...")
    career_df = master_df.groupby(['playerId', 'name']).agg(
        career_games=('games_played', 'sum'),
        career_hd_shots=('I_F_highDangerShots', 'sum'),
        career_total_shots=('I_F_shotsOnGoal', 'sum'),
        career_icetime=('icetime', 'sum'),
    ).reset_index()
    # 4. Calculate the career priors (per 60)
    # Avoid division by zero by adding a tiny safety net
    career_df['career_hd_per_60'] = career_df['career_hd_shots'] / (career_df['career_icetime'] / 3600 + 0.001)
    career_df['career_shots_per_60'] = career_df['career_total_shots'] / (career_df['career_icetime'] / 3600 + 0.001)

    # 5. Save to the career folder
    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    career_df.to_csv(OUTPUT_FILE, index=False)
    
    print(f"✅ Success! Saved {len(career_df)} player career priors to {OUTPUT_FILE}")

if __name__ == "__main__":
    trim_careerdefenders()
    trim_skater_season()
    build_career_data()


    
        
        