"""Streamlit UI: python -m streamlit run hearlike/app.py"""

import html
import math

import streamlit as st

from hearlike import similarity
from hearlike.cli import find_similar

st.set_page_config(page_title="hearlike", page_icon="🎧", layout="wide")

# ---------------------------------------------------------------------------
# Theme: deep charcoal, one violet -> cyan accent gradient, rounded cards.
# ---------------------------------------------------------------------------
st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

    html, body, [class*="css"], .stApp {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
    }
    .stApp {
        background:
            radial-gradient(1100px 550px at 85% -10%, rgba(139, 92, 246, 0.20), transparent 60%),
            radial-gradient(900px 500px at -10% 0%, rgba(34, 211, 238, 0.10), transparent 55%),
            #0d0d13;
        color: #eceef4;
    }
    [data-testid="stSidebar"] {
        background: #12121b;
        border-right: 1px solid rgba(255, 255, 255, 0.07);
    }
    [data-testid="stSidebar"] label, [data-testid="stSidebar"] p,
    [data-testid="stSidebar"] span, [data-testid="stSidebar"] div {
        color: #c9cdd8;
    }

    /* Hide default Streamlit chrome, tastefully. */
    #MainMenu { visibility: hidden; }
    footer { visibility: hidden; }
    [data-testid="stToolbar"] { display: none; }
    [data-testid="stDecoration"] { display: none; }
    header[data-testid="stHeader"] { background: transparent; }

    /* Hero */
    .hl-hero { text-align: center; padding: 1.6rem 1rem 0.4rem 1rem; }
    .hl-title {
        font-size: 3.4rem; font-weight: 800; letter-spacing: -0.035em; line-height: 1.05;
        background: linear-gradient(92deg, #a78bfa 0%, #818cf8 45%, #22d3ee 100%);
        -webkit-background-clip: text; background-clip: text; color: transparent;
        margin: 0;
    }
    .hl-tagline { font-size: 1.15rem; color: #e6e8f0; font-weight: 500; margin-top: 0.55rem; }
    .hl-caption { font-size: 0.9rem; color: #9aa0b4; max-width: 640px; margin: 0.45rem auto 0 auto; line-height: 1.55; }

    /* Cards */
    [data-testid="stVerticalBlockBorderWrapper"] {
        border-radius: 18px !important;
        border: 1px solid rgba(255, 255, 255, 0.09) !important;
        background: linear-gradient(180deg, rgba(255,255,255,0.045), rgba(255,255,255,0.02));
        box-shadow: 0 10px 34px rgba(0, 0, 0, 0.38);
    }
    [data-testid="stImage"] img { border-radius: 14px; }

    /* Buttons */
    .stButton > button { border-radius: 999px; font-weight: 600; }
    button[kind="primary"] {
        background: linear-gradient(92deg, #8b5cf6, #06b6d4);
        border: none; color: #ffffff; box-shadow: 0 6px 20px rgba(139, 92, 246, 0.35);
    }
    button[kind="primary"]:hover { filter: brightness(1.12); color: #ffffff; }
    [data-testid="stLinkButton"] a { border-radius: 999px; font-weight: 600; }

    /* Progress bars in the accent gradient */
    .stProgress > div > div > div > div {
        background-image: linear-gradient(90deg, #8b5cf6, #22d3ee);
        border-radius: 999px;
    }

    /* Seed card bits */
    .hl-eyebrow {
        font-size: 0.72rem; font-weight: 700; letter-spacing: 0.18em;
        color: #a78bfa; text-transform: uppercase; margin-bottom: 0.2rem;
    }
    .hl-seed-title { font-size: 1.9rem; font-weight: 800; letter-spacing: -0.02em; line-height: 1.15; color: #f4f5fa; overflow-wrap: anywhere; }
    .hl-seed-sub { font-size: 1.0rem; color: #c9cdd8; margin-top: 0.15rem; }
    .hl-seed-meta { font-size: 0.85rem; color: #9aa0b4; margin-top: 0.1rem; }
    .hl-stats { display: flex; gap: 0.7rem; flex-wrap: wrap; margin: 1rem 0 0.4rem 0; }
    .hl-stat {
        flex: 1 1 90px; background: rgba(255, 255, 255, 0.05);
        border: 1px solid rgba(255, 255, 255, 0.08); border-radius: 14px;
        padding: 0.65rem 0.8rem; text-align: center;
    }
    .hl-stat-value { font-size: 1.25rem; font-weight: 700; color: #ffffff; line-height: 1.2; }
    .hl-stat-label { font-size: 0.68rem; font-weight: 600; letter-spacing: 0.12em; text-transform: uppercase; color: #9aa0b4; margin-top: 0.15rem; }

    /* Result cards */
    .hl-rank {
        display: inline-block; font-weight: 800; font-size: 1.05rem; color: transparent;
        background: linear-gradient(92deg, #a78bfa, #22d3ee);
        -webkit-background-clip: text; background-clip: text; margin-right: 0.45rem;
    }
    .hl-track-title { font-size: 1.12rem; font-weight: 700; color: #f4f5fa; overflow-wrap: anywhere; }
    .hl-track-artist { font-size: 1.12rem; font-weight: 500; color: #b9bdd0; overflow-wrap: anywhere; }
    .hl-badge {
        float: right; margin-left: 0.6rem; font-size: 0.8rem; font-weight: 700; color: #ffffff;
        background: linear-gradient(92deg, #8b5cf6, #06b6d4);
        border-radius: 999px; padding: 0.22rem 0.7rem; white-space: nowrap;
        box-shadow: 0 4px 14px rgba(139, 92, 246, 0.35);
    }
    .hl-meta { font-size: 0.85rem; color: #9aa0b4; margin: 0.3rem 0 0.5rem 0; }
    .hl-chips { margin: 0.1rem 0 0.4rem 0; }
    .hl-chip {
        display: inline-block; font-size: 0.78rem; font-weight: 500; color: #ddd6fe;
        background: rgba(139, 92, 246, 0.14); border: 1px solid rgba(167, 139, 250, 0.35);
        border-radius: 999px; padding: 0.18rem 0.6rem; margin: 0 0.35rem 0.35rem 0;
    }
    .hl-art-fallback {
        display: flex; align-items: center; justify-content: center;
        width: 100%; aspect-ratio: 1 / 1; border-radius: 14px; font-size: 2.2rem;
        background: linear-gradient(135deg, rgba(139,92,246,0.35), rgba(34,211,238,0.25));
        border: 1px solid rgba(255,255,255,0.10);
    }

    /* Empty state */
    .hl-empty { text-align: center; padding: 3.2rem 1rem 2.6rem 1rem; }
    .hl-empty-art {
        width: 92px; height: 92px; margin: 0 auto 1.1rem auto; border-radius: 50%;
        display: flex; align-items: center; justify-content: center; font-size: 2.6rem;
        background: linear-gradient(135deg, rgba(139,92,246,0.30), rgba(34,211,238,0.22));
        border: 1px solid rgba(167, 139, 250, 0.45);
        box-shadow: 0 12px 34px rgba(139, 92, 246, 0.30);
    }
    .hl-empty-title { font-size: 1.35rem; font-weight: 700; color: #f4f5fa; }
    .hl-empty-sub { font-size: 0.92rem; color: #9aa0b4; margin-top: 0.35rem; }

    .hl-footer { text-align: center; font-size: 0.78rem; color: #6f7488; padding: 1.4rem 0 0.4rem 0; }
    </style>
    """,
    unsafe_allow_html=True,
)

# Component order/labels for the "Why this match" breakdown. similarity
# components are DISTANCES in 0..1 (0 = identical), so closeness = 1 - dist.
# Weights mirror similarity.WEIGHTS.
COMPONENTS = [
    ("tempo", "Tempo", 30),
    ("key", "Key", 25),
    ("timbre", "Timbre · texture", 25),
    ("energy", "Energy", 10),
    ("brightness", "Brightness", 10),
]


def hi_res(artwork_url: str | None) -> str:
    """artworkUrl100 -> 600x600 version for crisp cards."""
    if not artwork_url:
        return ""
    return artwork_url.replace("100x100", "600x600")


def stat_block(label: str, value: str) -> str:
    return (
        f'<div class="hl-stat"><div class="hl-stat-value">{value}</div>'
        f'<div class="hl-stat-label">{label}</div></div>'
    )


def _finite(value, default=None):
    """value as a finite float, else default (guards NaN/missing features)."""
    try:
        out = float(value)
    except (TypeError, ValueError):
        return default
    return out if math.isfinite(out) else default


def _clamp01(value) -> float:
    out = _finite(value, 0.0)
    return min(max(out, 0.0), 1.0)


def _fmt_bpm(feat: dict) -> str:
    tempo = _finite(feat.get("tempo"))
    return f"{tempo:.0f} BPM" if tempo is not None else "— BPM"


def _fmt_energy(feat: dict) -> str:
    energy = _finite(feat.get("energy"))
    return f"{energy:.3f}" if energy is not None else "—"


def _norm(text: str) -> str:
    return "".join(ch for ch in (text or "").lower() if ch.isalnum())


def dedupe_ranked(ranked: list, seed) -> list:
    """Drop display-level duplicates: the same song on a different album has
    a different trackId, so the pool builder can't catch it — and the seed
    itself can reappear that way. Ranked is best-first, so first wins."""
    seen = {(_norm(seed.title), _norm(seed.artist))}
    unique = []
    for item in ranked:
        key = (_norm(item[0].title), _norm(item[0].artist))
        if key in seen:
            continue
        seen.add(key)
        unique.append(item)
    return unique


def show_artwork(track) -> None:
    """Artwork with graceful fallbacks: hi-res, then original, then a tile."""
    for url in (hi_res(track.artwork), track.artwork):
        if not url:
            continue
        try:
            st.image(url, use_container_width=True)
            return
        except Exception:
            continue
    st.markdown('<div class="hl-art-fallback">🎵</div>', unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# Sidebar controls
# ---------------------------------------------------------------------------
with st.sidebar:
    st.markdown("### 🎧 hearlike")
    st.caption("Songs that *sound* alike — matched on the audio itself.")
    title = st.text_input("Song", value="Marvins Room")
    artist = st.text_input("Artist (optional)", value="Drake")
    extra = st.text_input(
        "Extra searches to widen the pool (comma separated)",
        value="PARTYNEXTDOOR, The Weeknd, Bryson Tiller",
    )
    limit = st.slider("Matches to show", 3, 20, 10)
    go = st.button("Find similar", type="primary", use_container_width=True)
    st.divider()
    st.markdown(
        "**How it works**  \n"
        "hearlike listens to each song's 30-second preview and measures its "
        "tempo, key, energy, brightness, and timbre (MFCC texture) — then ranks "
        "the pool by how close those measurements land. No genre tags, no "
        "collaborative filtering. First runs are slower while previews are "
        "analyzed; results are cached afterwards."
    )

# ---------------------------------------------------------------------------
# Hero
# ---------------------------------------------------------------------------
st.markdown(
    """
    <div class="hl-hero">
        <p class="hl-title">hearlike</p>
        <div class="hl-tagline">Find songs that sound like the one you love.</div>
        <div class="hl-caption">
            Matched by ear, not by tags — every candidate is scored on its actual
            audio: tempo, key, energy, brightness &amp; timbre, measured from
            30-second previews.
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

# ---------------------------------------------------------------------------
# Search (results cached in session state so widget reruns don't re-run it)
# ---------------------------------------------------------------------------
if go:
    title = title.strip()
    artist = artist.strip()
    if not title:
        st.session_state["hl_result"] = None
        st.session_state["hl_error"] = "Type a song name in the sidebar first."
    else:
        queries = [q.strip() for q in extra.split(",") if q.strip()]
        # Clear the previous result up front so a failed search never leaves
        # stale cards sitting under the new error.
        st.session_state["hl_result"] = None
        with st.spinner("Listening to previews… (first run analyzes each candidate)"):
            try:
                st.session_state["hl_result"] = find_similar(
                    title, artist or None, queries, limit, pool_cap=40
                )
                st.session_state["hl_error"] = None
                st.session_state["hl_search_key"] = (title, artist, extra, limit)
            except SystemExit as e:
                st.session_state["hl_error"] = str(e) or "That search failed."
            except Exception:
                st.session_state["hl_error"] = (
                    "Something went wrong while searching — check your "
                    "connection and try again."
                )

error = st.session_state.get("hl_error")
result = st.session_state.get("hl_result")

if error:
    st.error(error)

if result:
    seed, seed_feat, ranked = result

    # --- Seed card ---------------------------------------------------------
    with st.container(border=True):
        art_col, info_col = st.columns([1, 2.6])
        with art_col:
            show_artwork(seed)
        with info_col:
            st.markdown(
                '<div class="hl-eyebrow">Seed track</div>', unsafe_allow_html=True
            )
            st.markdown(
                f'<div class="hl-seed-title">{html.escape(seed.title or "Unknown title")}</div>',
                unsafe_allow_html=True,
            )
            st.markdown(
                f'<div class="hl-seed-sub">{html.escape(seed.artist or "Unknown artist")}</div>',
                unsafe_allow_html=True,
            )
            meta_bits = [b for b in (seed.album, seed.genre) if b]
            if meta_bits:
                st.markdown(
                    f'<div class="hl-seed-meta">'
                    f'{html.escape(" · ".join(meta_bits))}</div>',
                    unsafe_allow_html=True,
                )
            stats = [
                stat_block("Tempo", _fmt_bpm(seed_feat)),
                stat_block("Key", html.escape(str(seed_feat.get("key") or "—"))),
                stat_block("Energy", _fmt_energy(seed_feat)),
            ]
            brightness = _finite(seed_feat.get("brightness"))
            if brightness is not None:
                stats.append(stat_block("Brightness", f"{brightness:,.0f} Hz"))
            st.markdown(
                f'<div class="hl-stats">{"".join(stats)}</div>',
                unsafe_allow_html=True,
            )
            if seed.preview_url:
                st.audio(seed.preview_url)
            else:
                st.caption("No preview available for the seed track.")

    # --- Results -----------------------------------------------------------
    ranked = dedupe_ranked(ranked, seed)
    st.markdown("### Closest matches")
    st.caption(
        f"{len(ranked)} songs ranked by audio similarity to {seed.label()} — "
        "open “Why this match” on any card to see the component breakdown."
    )
    if st.session_state.get("hl_search_key") not in (
        None,
        (title.strip(), artist.strip(), extra, limit),
    ):
        st.caption("ℹ️ Search settings changed — press **Find similar** to refresh these results.")

    if not ranked:
        st.info("No candidates were found for that search — try widening the extra searches.")

    for rank, (track, feat, score, comps) in enumerate(ranked, start=1):
        score = _finite(score, 0.0)
        try:
            reasons = similarity.explain(seed_feat, feat, comps)
        except Exception:
            reasons = ["closest overall match in the pool"]
        with st.container(border=True):
            art_col, main_col = st.columns([1, 6])
            with art_col:
                show_artwork(track)
            with main_col:
                st.markdown(
                    f'<span class="hl-badge">{score:.0f}% match</span>'
                    f'<span class="hl-rank">#{rank}</span>'
                    f'<span class="hl-track-title">{html.escape(track.title or "Unknown title")}</span>'
                    f' <span class="hl-track-artist">— {html.escape(track.artist or "Unknown artist")}</span>',
                    unsafe_allow_html=True,
                )
                st.progress(_clamp01(score / 100.0))
                meta_bits = [
                    _fmt_bpm(feat),
                    html.escape(str(feat.get("key") or "—")),
                    f"energy {_fmt_energy(feat)}",
                ]
                if track.album:
                    meta_bits.append(html.escape(track.album))
                st.markdown(
                    f'<div class="hl-meta">{" · ".join(meta_bits)}</div>',
                    unsafe_allow_html=True,
                )
                chips = "".join(
                    f'<span class="hl-chip">{html.escape(r)}</span>' for r in reasons
                )
                st.markdown(
                    f'<div class="hl-chips">{chips}</div>', unsafe_allow_html=True
                )
                with st.expander("Why this match"):
                    st.caption(
                        "How alike the two songs are on each measured component "
                        "(share of the overall score in parentheses)."
                    )
                    for comp_key, comp_label, comp_weight in COMPONENTS:
                        dist = _finite(comps.get(comp_key))
                        if dist is None:
                            continue
                        closeness = _clamp01(1.0 - dist)
                        st.progress(
                            closeness,
                            text=f"{comp_label} — {closeness:.0%} alike ({comp_weight}% of score)",
                        )
                play_col, link_col = st.columns([4, 1.4])
                with play_col:
                    if track.preview_url:
                        st.audio(track.preview_url)
                    else:
                        st.caption("No preview available.")
                with link_col:
                    if track.store_url:
                        st.link_button(
                            "Open in Apple Music",
                            track.store_url,
                            use_container_width=True,
                        )
elif not error:
    # --- Empty state -------------------------------------------------------
    with st.container(border=True):
        st.markdown(
            """
            <div class="hl-empty">
                <div class="hl-empty-art">🎧</div>
                <div class="hl-empty-title">Search a song to hear its neighborhood</div>
                <div class="hl-empty-sub">
                    Pick a track in the sidebar and hearlike will map the songs
                    that live closest to it in tempo, key, energy, brightness
                    and timbre.
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

st.markdown(
    '<div class="hl-footer">hearlike · features measured from 30-second iTunes previews</div>',
    unsafe_allow_html=True,
)
