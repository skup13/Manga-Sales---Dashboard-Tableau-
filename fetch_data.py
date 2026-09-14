import os
import requests
import pandas as pd
from dotenv import load_dotenv

load_dotenv()
client_id = os.environ.get('MAL_CLIENT_ID')
headers = {'X-MAL-Client-ID': client_id}

FIELDS = 'genres,start_date,num_episodes,mean,studios,authors{first_name,last_name},num_volumes'

def fetch_ranking(media_type, ranking_type, limit=200):
    url = f'https://api.myanimelist.net/v2/{media_type}/ranking?ranking_type={ranking_type}&limit={limit}&fields={FIELDS}'
    response = requests.get(url, headers=headers)
    return response.json().get('data', []) if response.status_code == 200 else []

print("📡 Gathering All-Time Legends and Recent Releases...")

# 1. Pull All-Time Top AND Recent Ongoing Data
anime_all_time = fetch_ranking('anime', 'all', limit=200)
anime_recent   = fetch_ranking('anime', 'airing', limit=200) # Currently broadcasting now

manga_all_time = fetch_ranking('manga', 'all', limit=200)
manga_recent   = fetch_ranking('manga', 'manga', limit=200)  # Active serializations matching modern releases

# 2. Parse Anime and flag where they came from
anime_rows = {}
for era, dataset in [('All-Time', anime_all_time), ('Recent/Airing', anime_recent)]:
    for item in dataset:
        node = item.get('node', {})
        title = node.get('title')
        
        if title not in anime_rows:
            anime_rows[title] = {
                'Title': title, 'Score': node.get('mean'), 'Release_Date': node.get('start_date'),
                'Episodes': node.get('num_episodes'), 'Genres': [g.get('name') for g in node.get('genres', [])],
                'Studios': [s.get('name') for s in node.get('studios', [])], 'Era_Category': era
            }
        else:
            anime_rows[title]['Era_Category'] = 'Both Eras'

# 3. Parse Manga and flag where they came from
manga_rows = {}
for era, dataset in [('All-Time', manga_all_time), ('Recent/Serialized', manga_recent)]:
    for item in dataset:
        node = item.get('node', {})
        title = node.get('title')
        
        if title not in manga_rows:
            author_list = [f"{a.get('node', {}).get('first_name', '')} {a.get('node', {}).get('last_name', '')}".strip() for a in node.get('authors', [])]
            manga_rows[title] = {
                'Title': title, 'Score': node.get('mean'), 'Release_Date': node.get('start_date'),
                'Volumes': node.get('num_volumes'), 'Genres': [g.get('name') for g in node.get('genres', [])],
                'Authors': [name for name in author_list if name], 'Era_Category': era
            }
        else:
            manga_rows[title]['Era_Category'] = 'Both Eras'

# 4. Save clean dataframes to CSV files
df_anime = pd.DataFrame(anime_rows.values())
df_manga = pd.DataFrame(manga_rows.values())

df_anime.to_csv("master_anime_warehouse.csv", index=False)
df_manga.to_csv("master_manga_warehouse.csv", index=False)

print(f"\n🎉 Success! Anime Database saved with {len(df_anime)} unique rows.")
print(f"🎉 Success! Manga Database saved with {len(df_manga)} unique rows.")