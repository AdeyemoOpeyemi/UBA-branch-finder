import pandas as pd
import requests
import streamlit as st
from rapidfuzz import process  # For fuzzy matching

# ---------------- Load Dataset ----------------
@st.cache_data
def load_data():
    file_path = r"C:\Users\USER\Desktop\Testing\R_conversion\uba_branches.csv"
    try:
        df = pd.read_csv(file_path)
        # Filter only Nigeria if COUNTRY column exists
        if "COUNTRY" in df.columns:
            df = df[df["COUNTRY"].str.lower() == "nigeria"]
        return df
    except FileNotFoundError:
        st.error(f"❌ Dataset not found: {file_path}")
        return None

# ---------------- Free Geocoding with Nominatim ----------------
def geocode_address(address):
    url = "https://nominatim.openstreetmap.org/search"
    params = {"q": address, "format": "json", "limit": 1, "countrycodes": "ng"}
    response = requests.get(url, params=params, headers={"User-Agent": "UBABranchFinder"})
    data = response.json()
    if data:
        return float(data[0]["lat"]), float(data[0]["lon"])
    return None, None

# ---------------- Fuzzy Search in Dataset ----------------
def search_dataset(df, query, threshold=60):
    if df is not None:
        query = query.lower().strip()
        choices = df.apply(lambda row: row.astype(str).str.lower().to_string(), axis=1).tolist()
        matches = process.extract(query, choices, limit=5, score_cutoff=threshold)
        if matches:
            matched_indices = [m[2] for m in matches]
            return df.iloc[matched_indices], matches
    return None, None

# ---------------- Global Search (Nigeria only in OSM) ----------------
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

# ---------------- Store Results in Session ----------------
def add_to_history(query, result_text, dataset_results=None, osm_results=None):
    coords = []
    if dataset_results is not None:
        for _, row in dataset_results.iterrows():
            address = f"{row.get('BRANCH ADDRESS','')}, {row.get('STATE','')}, {row.get('COUNTRY','')}"
            lat, lon = geocode_address(address)
            if lat and lon:
                coords.append({"lat": lat, "lon": lon, "Branch": row.get("BRANCH NAME", "N/A")})

    st.session_state["search_results"].append({
        "query": query,
        "text": result_text,
        "data": dataset_results if dataset_results is not None else osm_results,
        "map": pd.DataFrame(coords) if coords else (osm_results.rename(columns={"Lat": "lat", "Lon": "lon"}) if osm_results is not None else None)
    })

# ---------------- Streamlit UI ----------------
st.title("🏦 UBA Branch Finder (Nigeria Only)")

df = load_data()
if df is not None:
    st.success("✅ UBA Dataset loaded successfully (Nigeria only)!")

# Initialize search history
if "search_results" not in st.session_state:
    st.session_state["search_results"] = []

# ---------------- Main Input ----------------
query = st.text_input("🔎 Enter a Nigerian state, city, or branch name:")

if st.button("Search"):
    if query:
        dataset_results, matches = search_dataset(df, query)

        if dataset_results is not None and not dataset_results.empty:
            if matches:
                top_match, score, _ = matches[0]

                if score > 85:  # confident → auto-correct
                    corrected_query = top_match
                    st.info(f"🔄 Auto-corrected to: **{corrected_query}** (confidence: {score}%)")
                    add_to_history(corrected_query, f"🏦 Branches found in UBA dataset for: {corrected_query}", dataset_results)

                else:  # show ranked suggestions
                    st.warning("⚠️ Did you mean one of these?")
                    for i, (text, conf, _) in enumerate(matches, 1):
                        col1, col2 = st.columns([3, 1])
                        with col1:
                            st.write(f"{i}. **{text}** (confidence: {conf}%)")
                        with col2:
                            if st.button(f"Search '{text}'", key=f"suggest_{i}"):
                                add_to_history(text, f"🏦 Branches found in UBA dataset for: {text}", dataset_results)

            else:
                add_to_history(query, f"🏦 Branches found in UBA dataset for: {query}", dataset_results)

        else:
            # Fallback → OSM Nigeria only
            osm_results = search_osm(query)
            if osm_results is not None and not osm_results.empty:
                add_to_history(query, f"🌍 No dataset match, searching in Nigeria (OSM) for: {query}", osm_results=osm_results)
            else:
                add_to_history(query, f"❌ No results found in Nigeria for: {query}")
    else:
        st.warning("Please enter a search query.")

# ---------------- Sidebar for History ----------------
st.sidebar.title("🕘 Search History with Results")

if st.sidebar.button("🗑️ Clear History"):
    st.session_state["search_results"] = []
    st.sidebar.success("History cleared!")

if st.session_state["search_results"]:
    for i, res in enumerate(st.session_state["search_results"], 1):
        st.sidebar.markdown(f"### {i}. {res['query']}")
        st.sidebar.markdown(res['text'])
        if res["data"] is not None:
            st.sidebar.dataframe(res["data"])
        if res["map"] is not None and not res["map"].empty:
            st.sidebar.map(res["map"])
        st.sidebar.markdown("---")
else:
    st.sidebar.info("No searches yet. Start by entering a Nigerian location above!")
