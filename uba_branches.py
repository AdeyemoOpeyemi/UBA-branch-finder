import pandas as pd
import requests
from rapidfuzz import process

# ---------------- Load Dataset ----------------
def load_data(file_path):
    try:
        df = pd.read_csv(file_path)
        if "COUNTRY" in df.columns:
            df = df[df["COUNTRY"].str.lower() == "nigeria"]
        return df
    except FileNotFoundError:
        print(f"❌ Dataset not found: {file_path}")
        return None

# ---------------- Geocoding ----------------
def geocode_address(address):
    url = "https://nominatim.openstreetmap.org/search"
    params = {"q": address, "format": "json", "limit": 1, "countrycodes": "ng"}
    response = requests.get(url, params=params, headers={"User-Agent": "UBABranchFinder"})
    data = response.json()
    if data:
        return float(data[0]["lat"]), float(data[0]["lon"])
    return None, None

# ---------------- Fuzzy Search ----------------
def search_dataset(df, query, threshold=60):
    if df is not None:
        query = query.lower().strip()
        choices = df.apply(lambda row: row.astype(str).str.lower().to_string(), axis=1).tolist()
        matches = process.extract(query, choices, limit=5, score_cutoff=threshold)
        if matches:
            matched_indices = [m[2] for m in matches]
            return df.iloc[matched_indices], matches
    return None, None

# ---------------- Global OSM Search ----------------
def search_osm(query):
    url = "https://nominatim.openstreetmap.org/search"
    params = {"q": query, "format": "json", "limit": 5, "countrycodes": "ng"}
    response = requests.get(url, params=params, headers={"User-Agent": "UBABranchFinder"})
    data = response.json()
    if data:
        places = []
        for place in data:
            places.append({
                "Name": place.get("display_name"),
                "Lat": float(place["lat"]),
                "Lon": float(place["lon"])
            })
        return pd.DataFrame(places)
    return None

# ---------------- Main Program ----------------
def main():
    file_path = r"C:\Users\USER\Desktop\Testing\R_conversion\uba_branches.csv"
    df = load_data(file_path)
    if df is None:
        return

    print("✅ UBA Dataset loaded successfully (Nigeria only)!\n")
    
    search_history = []

    while True:
        query = input("🔎 Enter a Nigerian state, city, or branch name (or type 'exit' to quit): ").strip()
        if query.lower() == 'exit':
            print("\nSearch history:")
            for i, h in enumerate(search_history, 1):
                print(f"{i}. {h}")
            break

        dataset_results, matches = search_dataset(df, query)
        if dataset_results is not None and not dataset_results.empty:
            if matches:
                top_match, score, _ = matches[0]
                if score > 85:
                    corrected_query = top_match
                    print(f"🔄 Auto-corrected to: {corrected_query} (confidence: {score}%)")
                    search_history.append(f"Branches found in dataset for: {corrected_query}")
                    print(dataset_results)
                else:
                    print("⚠️ Did you mean one of these?")
                    for i, (text, conf, _) in enumerate(matches, 1):
                        print(f"{i}. {text} (confidence: {conf}%)")
                    search_history.append(f"Branches found in dataset for: {query}")
                    print(dataset_results)
        else:
            # fallback → OSM search
            osm_results = search_osm(query)
            if osm_results is not None and not osm_results.empty:
                print("🌍 No dataset match. Results from OSM Nigeria:")
                print(osm_results)
                search_history.append(f"OSM search for: {query}")
            else:
                print(f"❌ No results found in Nigeria for: {query}")
                search_history.append(f"No results found for: {query}")

if __name__ == "__main__":
    main()
