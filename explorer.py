# explorer.py
# Streamlit app to filter quotes by year/house/frame and export selections.

import streamlit as st, json, pandas as pd

st.set_page_config(page_title="Hansard Quote Bank", layout="wide")

@st.cache_data
def load_data(path="quotes_frame_targeted.jsonl"):
    rows=[]
    with open(path, "r", encoding="utf-8") as f:
        for ln in f:
            rows.append(json.loads(ln))
    df = pd.DataFrame(rows)
    df["year"] = pd.to_datetime(df["date"]).dt.year
    return df

df = load_data()

st.title("Hansard Quote Bank — Immigration × Labour (19th–mid 20th c.)")

col1, col2, col3, col4 = st.columns(4)
min_year = int(df.year.min())
max_year = int(df.year.max())
if min_year == max_year:
    years = col1.selectbox("Year", [min_year])
    years = (years, years)  # Convert to tuple for consistency
else:
    years = col1.slider("Year range", min_year, max_year, (min_year, max_year))
house = col2.multiselect("House", sorted(df.house.dropna().unique().tolist()), default=df.house.dropna().unique().tolist())
frames = col3.multiselect("Frame", ["LABOUR_NEED","LABOUR_THREAT","RACIALISED","MIXED","OTHER"], default=["LABOUR_NEED","LABOUR_THREAT","RACIALISED","MIXED"])
search = col4.text_input("Search inside quotes (optional)")

view = df[(df.year.between(years[0], years[1])) & (df.house.isin(house)) & (df.frame.isin(frames))]
if search:
    view = view[view.quote.str.contains(search, case=False, na=False)]

st.write(f"Results: {len(view)}")
st.dataframe(view[["date","house","member","party","frame","debate_title","quote","hansard_url"]], use_container_width=True, height=600)

st.download_button("Download current view as CSV", data=view.to_csv(index=False).encode("utf-8"),
                   file_name="quotes_filtered.csv", mime="text/csv")