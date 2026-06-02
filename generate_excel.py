import pandas as pd
from io import StringIO

# Data CSV mentah
csv_data = """date,home_team,away_team,home_goals,away_goals,home_goalscorers,away_goalscorers,league,season,venue,referee,outcome_type,home_penalty_score,away_penalty_score,home_penalty_takers,away_penalty_takers,home_possession,away_possession,home_total_shots,away_total_shots,home_shots_on_target,away_shots_on_target,home_shots_off_target,away_shots_off_target,home_total_passes,away_total_passes,home_pass_accuracy,away_pass_accuracy,home_corners,away_corners,home_fouls,away_fouls,home_yellow_cards,away_yellow_cards,home_red_cards,away_red_cards,home_xg,away_xg,home_tackles,away_tackles,home_interceptions,away_interceptions,home_offsides,away_offsides,home_goalkeeper_saves,away_goalkeeper_saves,home_long_balls,away_long_balls,home_long_balls_success,away_long_balls_success,home_passes_final_third_succes,away_passes_final_third_succes,home_passes_final_third,away_passes_final_third,home_passes_into_penalty_area,away_passes_into_penalty_area,home_throw_ins,away_throw_ins,home_through_balls,away_through_balls,home_final_third_entries,away_final_third_entries,home_crosses,away_crosses,home_crosses_success,away_crosses_success,home_dribbles_attempted,away_dribbles_attempted,home_dribbles_succeeded,away_dribbles_succeeded,home_blocks,away_blocks,home_shots_inside_box,away_shots_inside_box,home_shots_outside_box,away_shots_outside_box,home_big_chances_scored,away_big_chances_scored,home_big_chances_missed,away_big_chances_missed,home_hit_woodwork,away_hit_woodwork,home_tackles_success,away_tackles_success,home_tackles_total,away_tackles_total,home_clearances,away_clearances,home_duels_won,away_duels_won,home_duels_total,away_duels_total,home_takles,away_takles
2026-07-10,Barcelona,Real Madrid,3,1,"Lewandowski 15', Pedri 45', Yamal 80'",Bellingham 33',La Liga,2025/2026,Camp Nou,Mateu Lahoz,FT,,,,,,60,40,18,12,7,4,6,5,650,450,88,82,6,4,10,12,2,3,0,0,2.45,1.12,15,18,10,12,2,3,3,5,40,35,25,18,120,80,150,110,15,8,20,18,5,3,40,25,15,10,5,3,20,15,12,8,3,4,12,8,6,4,3,1,2,1,1,0,12,14,18,22,15,20,45,40,90,85,12,14
2026-07-15,Arsenal,Bayern Munich,1,1,Saka 45',Kane 60',Champions League,2025/2026,Emirates Stadium,Szymon Marciniak,PEN,5,4,"Saka ✅, Odegaard ✅, Rice ✅, Havertz ✅, Martinelli ✅","Kane ✅, Kimmich ✅, Sane ❌, Muller ✅, Musiala ✅",50,50,12,14,5,6,5,6,500,520,85,86,5,7,12,11,1,2,0,0,1.20,1.55,16,14,12,10,1,2,5,4,45,50,22,28,100,110,130,140,10,12,22,20,4,6,35,38,18,22,6,8,25,20,14,11,4,5,8,9,4,5,1,1,1,2,0,1,14,12,20,18,18,15,50,48,95,92,14,12"""

# Ubah string CSV menjadi DataFrame
df = pd.read_csv(StringIO(csv_data))

# Simpan langsung sebagai Excel
nama_file = "full_test_fdis.xlsx"
df.to_excel(nama_file, index=False)

print(f"✅ Berhasil! File {nama_file} sudah siap di-upload.")