"""Streamlit UI: python -m streamlit run hearlike/app.py"""

import streamlit as st

from hearlike import similarity
from hearlike.cli import find_similar

st.set_page_config(page_title="hearlike", page_icon="🎧")
st.title("🎧 hearlike")
st.write(
    "Find songs that sound like a song you like — by listening to the audio, "
    "not by reading genre tags. Features are measured from 30-second previews."
)

title = st.text_input("Song", value="Marvins Room")
artist = st.text_input("Artist (optional)", value="Drake")
extra = st.text_input(
    "Extra searches to widen the pool (comma separated)",
    value="PARTYNEXTDOOR, The Weeknd, Bryson Tiller",
)
limit = st.slider("Matches to show", 3, 20, 10)

if st.button("Find songs that sound like this"):
    queries = [q.strip() for q in extra.split(",") if q.strip()]
    with st.spinner("Listening to previews… (first run analyzes each candidate)"):
        try:
            seed, seed_feat, ranked = find_similar(
                title, artist or None, queries, limit, pool_cap=40
            )
        except SystemExit as e:
            st.error(str(e))
            st.stop()
    st.subheader(f"Seed: {seed.label()}")
    st.write(
        f"{seed_feat['tempo']:.0f} BPM · {seed_feat['key']} · "
        f"energy {seed_feat['energy']:.3f}"
    )
    if seed.preview_url:
        st.audio(seed.preview_url)
    for track, feat, score, comps in ranked:
        reasons = "; ".join(similarity.explain(seed_feat, feat, comps))
        st.markdown(f"**{score:.0f}% — {track.label()}**")
        st.write(f"{feat['tempo']:.0f} BPM · {feat['key']} · {reasons}")
        if track.preview_url:
            st.audio(track.preview_url)
        st.markdown(f"[Open in Apple Music]({track.store_url})")
