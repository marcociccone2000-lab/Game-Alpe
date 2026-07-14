"""
Alpe Games
----------
A fun community voting platform for funny moments, challenges and stories.
Run with:  streamlit run app.py
"""

import os
import uuid
from datetime import datetime, date

import pandas as pd
import plotly.express as px
import streamlit as st

import database as db

# ----------------------------------------------------------------------
# Page config
# ----------------------------------------------------------------------
st.set_page_config(
    page_title="Alpe Games",
    page_icon="🍺",
    layout="wide",
    initial_sidebar_state="expanded",
)

db.init_db()

ADMIN_PASSWORD = "alpe2026"  # change this to whatever you like

STAR_OPTIONS = {
    "⭐ (1)": 1,
    "⭐⭐ (2)": 2,
    "⭐⭐⭐ (3)": 3,
    "⭐⭐⭐⭐ (4)": 4,
    "⭐⭐⭐⭐⭐ (5)": 5,
}


# ----------------------------------------------------------------------
# Session state setup
# ----------------------------------------------------------------------
if "session_id" not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())

if "page" not in st.session_state:
    st.session_state.page = "🏠 Home"

if "selected_event" not in st.session_state:
    st.session_state.selected_event = None

if "admin_ok" not in st.session_state:
    st.session_state.admin_ok = False


def go_to(page_name, event_id=None):
    st.session_state.page = page_name
    if event_id is not None:
        st.session_state.selected_event = event_id


# ----------------------------------------------------------------------
# Small helpers
# ----------------------------------------------------------------------
def save_uploaded_image(uploaded_file):
    if uploaded_file is None:
        return None
    ext = os.path.splitext(uploaded_file.name)[1]
    filename = f"{uuid.uuid4().hex}{ext}"
    full_path = os.path.join(db.UPLOAD_DIR, filename)
    with open(full_path, "wb") as f:
        f.write(uploaded_file.getbuffer())
    return os.path.join("uploads", filename)


def image_or_placeholder(rel_path, width=None):
    if rel_path and os.path.exists(os.path.join(db.BASE_DIR, rel_path)):
        st.image(os.path.join(db.BASE_DIR, rel_path), width=width, use_container_width=(width is None))
    else:
        st.info("📷 No photo")


def medal(position):
    return {1: "🥇", 2: "🥈", 3: "🥉"}.get(position, f"#{position}")


def rating_stars(avg):
    full = int(round(avg))
    full = max(0, min(5, full))
    return "⭐" * full + "▫️" * (5 - full)


# ----------------------------------------------------------------------
# Sidebar navigation
# ----------------------------------------------------------------------
with st.sidebar:
    st.markdown("## 🏔️ Alpe Games")
    st.caption("Vote the funniest moment. Win the beer. 🍺")
    st.divider()

    pages = ["🏠 Home", "➕ Add Event", "🖼️ Gallery", "🏆 Leaderboard", "📊 Statistics", "🛠️ Admin"]
    choice = st.radio("Navigate", pages, index=pages.index(st.session_state.page), label_visibility="collapsed")
    if choice != st.session_state.page:
        st.session_state.page = choice
        st.session_state.selected_event = None

    st.divider()
    stats = db.get_stats_summary()
    st.metric("Events", stats["total_events"])
    st.metric("Votes", stats["total_votes"])
    st.metric("Avg rating", stats["avg_rating"])


# ----------------------------------------------------------------------
# HOME PAGE
# ----------------------------------------------------------------------
def page_home():
    st.markdown(
        """
        <div style="text-align:center; padding: 10px 0 0 0;">
            <h1 style="font-size:3rem; margin-bottom:0;">🏔️ Alpe Games 🍺</h1>
            <p style="font-size:1.2rem; color:gray;">Upload your funniest moments. Let the community decide. The winner drinks free.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.divider()

    stats = db.get_stats_summary()
    board = db.get_leaderboard_df()

    col1, col2, col3 = st.columns(3)
    col1.metric("📸 Total Events", stats["total_events"])
    col2.metric("🗳️ Total Votes", stats["total_votes"])
    col3.metric("⭐ Average Rating", stats["avg_rating"])

    st.write("")

    # Beer winner section
    st.subheader("🍺 Current Beer Winner")
    winners = board[board["total_votes"] > 0]
    if winners.empty:
        st.info("No votes yet — cast the first vote to crown a winner!")
    else:
        winner = winners.iloc[0]
        with st.container(border=True):
            wc1, wc2 = st.columns([1, 2])
            with wc1:
                image_or_placeholder(winner["image_path"], width=280)
            with wc2:
                st.markdown(f"### 🏆 {winner['title']}")
                st.write(winner["description"] or "")
                st.write(f"**Author:** {winner['author'] or 'Anonymous'}")
                st.write(f"**Average rating:** {rating_stars(winner['average_rating'])}  ({winner['average_rating']}/5)")
                st.write(f"**Total votes:** {winner['total_votes']}")
                st.success("This event is currently winning the 🍺!")

    st.write("")
    st.subheader("🏆 Top 3 Podium")
    top3 = board.head(3)
    if top3.empty:
        st.info("No events yet. Be the first to add one!")
    else:
        cols = st.columns(len(top3))
        for i, (_, row) in enumerate(top3.iterrows()):
            with cols[i]:
                with st.container(border=True):
                    st.markdown(f"<h2 style='text-align:center'>{medal(int(row['position']))}</h2>", unsafe_allow_html=True)
                    image_or_placeholder(row["image_path"], width=200)
                    st.markdown(f"**{row['title']}**")
                    st.caption(row["author"] or "Anonymous")
                    st.write(f"{rating_stars(row['average_rating'])} ({row['average_rating']}/5)")
                    st.caption(f"{row['total_votes']} votes")


# ----------------------------------------------------------------------
# ADD EVENT PAGE
# ----------------------------------------------------------------------
def page_add_event():
    st.header("➕ Add New Event")
    st.caption("Share your funniest moment, challenge or story with the group.")

    with st.form("add_event_form", clear_on_submit=True):
        title = st.text_input("Event Title *")
        description = st.text_area("Event Description *", height=140)
        photo = st.file_uploader("Photo Upload", type=["png", "jpg", "jpeg", "gif", "webp"])
        author = st.text_input("Author Name *")
        event_date = st.date_input("Event Date", value=date.today())

        submitted = st.form_submit_button("🚀 Submit Event", use_container_width=True)

        if submitted:
            if not title.strip() or not description.strip() or not author.strip():
                st.error("Please fill in Title, Description and Author before submitting.")
            else:
                image_path = save_uploaded_image(photo)
                new_id = db.add_event(title.strip(), description.strip(), image_path, author.strip(), event_date)
                st.success(f"🎉 Event '{title}' added successfully!")
                st.balloons()
                go_to("🖼️ Gallery", event_id=new_id)
                st.rerun()


# ----------------------------------------------------------------------
# VOTING WIDGET (shared by gallery + detail view)
# ----------------------------------------------------------------------
def voting_widget(event_id, key_prefix=""):
    already_voted = db.has_voted(event_id, st.session_state.session_id)
    if already_voted:
        st.info("✅ You already voted for this event. Thanks for participating!")
        return

    choice = st.radio(
        "Rate this event",
        list(STAR_OPTIONS.keys()),
        horizontal=True,
        key=f"{key_prefix}_rate_{event_id}",
        label_visibility="collapsed",
    )
    if st.button("Submit vote 🗳️", key=f"{key_prefix}_vote_btn_{event_id}"):
        rating = STAR_OPTIONS[choice]
        ok = db.add_vote(event_id, st.session_state.session_id, rating)
        if ok:
            st.success("Vote recorded! Thanks 🙌")
            st.rerun()
        else:
            st.warning("You already voted for this event.")


# ----------------------------------------------------------------------
# GALLERY PAGE
# ----------------------------------------------------------------------
def page_gallery():
    st.header("🖼️ Event Gallery")

    board = db.get_leaderboard_df()
    if board.empty:
        st.info("No events yet. Go to **➕ Add Event** to create the first one!")
        return

    search = st.text_input("🔎 Search by title or author")
    if search:
        mask = board["title"].str.contains(search, case=False, na=False) | board["author"].str.contains(
            search, case=False, na=False
        )
        board = board[mask]

    cols = st.columns(3)
    for i, (_, row) in enumerate(board.iterrows()):
        with cols[i % 3]:
            with st.container(border=True):
                image_or_placeholder(row["image_path"])
                st.markdown(f"**{medal(int(row['position']))} — {row['title']}**")
                st.caption(f"By {row['author'] or 'Anonymous'} · {row['event_date']}")
                st.write(row["description"][:120] + ("…" if len(str(row["description"])) > 120 else ""))
                st.write(f"{rating_stars(row['average_rating'])}  {row['average_rating']}/5 · {row['total_votes']} votes")

                if st.button("View & Vote 👉", key=f"view_{row['id']}", use_container_width=True):
                    go_to("Event Detail", event_id=int(row["id"]))
                    st.rerun()

    if st.session_state.page == "Event Detail" and st.session_state.selected_event:
        st.divider()
        page_event_detail(st.session_state.selected_event)


# ----------------------------------------------------------------------
# EVENT DETAIL VIEW
# ----------------------------------------------------------------------
def page_event_detail(event_id):
    event = db.get_event(event_id)
    if not event:
        st.error("Event not found.")
        return

    board = db.get_leaderboard_df()
    row = board[board["id"] == event_id]
    position = int(row["position"].iloc[0]) if not row.empty else None
    avg_rating = float(row["average_rating"].iloc[0]) if not row.empty else 0.0
    total_votes = int(row["total_votes"].iloc[0]) if not row.empty else 0

    st.subheader(f"{medal(position) if position else ''} {event['title']}")

    c1, c2 = st.columns([1, 1])
    with c1:
        image_or_placeholder(event["image_path"])
    with c2:
        st.write(event["description"])
        st.write(f"**Author:** {event['author'] or 'Anonymous'}")
        st.write(f"**Date:** {event['event_date']}")
        st.write(f"**Average rating:** {rating_stars(avg_rating)} ({avg_rating}/5)")
        st.write(f"**Total votes:** {total_votes}")
        if position:
            st.write(f"**Leaderboard position:** {medal(position)}")
        st.divider()
        voting_widget(event_id, key_prefix="detail")

    if st.button("⬅ Back to Gallery"):
        st.session_state.page = "🖼️ Gallery"
        st.session_state.selected_event = None
        st.rerun()


# ----------------------------------------------------------------------
# LEADERBOARD PAGE
# ----------------------------------------------------------------------
def page_leaderboard():
    st.header("🏆 Live Leaderboard")

    board = db.get_leaderboard_df()
    if board.empty:
        st.info("No events yet.")
        return

    display = board[["position", "title", "author", "average_rating", "total_votes"]].copy()
    display.columns = ["Position", "Event", "Author", "Score (avg ⭐)", "Votes"]
    display["Position"] = display["Position"].apply(lambda p: medal(int(p)))

    def highlight_top3(row):
        idx = row.name
        if idx == 0:
            return ["background-color: #FFF3CD"] * len(row)
        elif idx == 1:
            return ["background-color: #E9ECEF"] * len(row)
        elif idx == 2:
            return ["background-color: #F4E3D7"] * len(row)
        return [""] * len(row)

    st.dataframe(
        display.style.apply(highlight_top3, axis=1),
        use_container_width=True,
        hide_index=True,
    )

    st.caption("Ranking = highest average rating first, ties broken by number of votes.")


# ----------------------------------------------------------------------
# STATISTICS PAGE
# ----------------------------------------------------------------------
def page_statistics():
    st.header("📊 Statistics & Analytics")

    stats = db.get_stats_summary()
    board = db.get_leaderboard_df()
    votes = db.get_all_votes()

    c1, c2, c3 = st.columns(3)
    c1.metric("Total Events", stats["total_events"])
    c2.metric("Total Votes", stats["total_votes"])
    c3.metric("Average Rating", stats["avg_rating"])

    st.divider()

    if board.empty:
        st.info("No data yet. Add events and votes to see charts here.")
        return

    st.subheader("Top 10 Leaderboard")
    top10 = board.head(10)[["position", "title", "average_rating", "total_votes"]]
    top10.columns = ["Position", "Event", "Avg Rating", "Votes"]
    st.dataframe(top10, use_container_width=True, hide_index=True)

    st.divider()
    st.subheader("Votes per Event")
    fig1 = px.bar(
        board.sort_values("total_votes", ascending=False),
        x="title",
        y="total_votes",
        labels={"title": "Event", "total_votes": "Votes"},
        color="total_votes",
        color_continuous_scale="Blues",
    )
    fig1.update_layout(xaxis_tickangle=-30)
    st.plotly_chart(fig1, use_container_width=True)

    st.subheader("Ratings Distribution")
    if not votes.empty:
        fig2 = px.histogram(
            votes,
            x="rating",
            nbins=5,
            labels={"rating": "Star Rating"},
            color_discrete_sequence=["#F4A300"],
        )
        fig2.update_layout(bargap=0.2, xaxis=dict(dtick=1))
        st.plotly_chart(fig2, use_container_width=True)
    else:
        st.info("No votes cast yet.")

    st.subheader("Ranking Performance")
    fig3 = px.bar(
        board.sort_values("average_rating", ascending=True),
        x="average_rating",
        y="title",
        orientation="h",
        labels={"title": "Event", "average_rating": "Average Rating"},
        color="average_rating",
        color_continuous_scale="Viridis",
    )
    st.plotly_chart(fig3, use_container_width=True)


# ----------------------------------------------------------------------
# ADMIN PAGE
# ----------------------------------------------------------------------
def page_admin():
    st.header("🛠️ Admin Tools")

    if not st.session_state.admin_ok:
        pwd = st.text_input("Admin password", type="password")
        if st.button("Login"):
            if pwd == ADMIN_PASSWORD:
                st.session_state.admin_ok = True
                st.rerun()
            else:
                st.error("Wrong password.")
        st.stop()

    st.success("Logged in as Admin.")
    if st.button("Log out"):
        st.session_state.admin_ok = False
        st.rerun()

    st.divider()

    board = db.get_leaderboard_df()
    if board.empty:
        st.info("No events yet.")
        return

    event_titles = {f"{r['id']} — {r['title']}": r["id"] for _, r in board.iterrows()}

    tab_edit, tab_delete, tab_reset, tab_export = st.tabs(
        ["✏️ Edit Event", "🗑️ Delete Event", "♻️ Reset Votes", "📤 Export CSV"]
    )

    # --- Edit ---
    with tab_edit:
        selected = st.selectbox("Select event to edit", list(event_titles.keys()), key="edit_select")
        if selected:
            event = db.get_event(event_titles[selected])
            with st.form("edit_event_form"):
                new_title = st.text_input("Title", value=event["title"])
                new_desc = st.text_area("Description", value=event["description"] or "")
                new_author = st.text_input("Author", value=event["author"] or "")
                try:
                    default_date = datetime.strptime(event["event_date"], "%Y-%m-%d").date()
                except (ValueError, TypeError):
                    default_date = date.today()
                new_date = st.date_input("Date", value=default_date)
                new_photo = st.file_uploader("Replace photo (optional)", type=["png", "jpg", "jpeg", "gif", "webp"])

                if st.form_submit_button("💾 Save changes"):
                    new_image_path = save_uploaded_image(new_photo) if new_photo else None
                    db.update_event(event["id"], new_title, new_desc, new_author, new_date, new_image_path)
                    st.success("Event updated.")
                    st.rerun()

    # --- Delete ---
    with tab_delete:
        selected = st.selectbox("Select event to delete", list(event_titles.keys()), key="delete_select")
        if selected:
            st.warning("This will permanently remove the event and its votes.")
            if st.button("🗑️ Confirm delete", key="confirm_delete"):
                db.delete_event(event_titles[selected])
                st.success("Event deleted.")
                st.rerun()

    # --- Reset ---
    with tab_reset:
        st.write("Reset votes for a single event, or wipe the whole leaderboard.")
        selected = st.selectbox("Select event to reset votes for", list(event_titles.keys()), key="reset_select")
        if st.button("Reset votes for this event"):
            db.reset_votes_for_event(event_titles[selected])
            st.success("Votes reset for this event.")
            st.rerun()

        st.divider()
        st.write("**Danger zone**")
        colA, colB = st.columns(2)
        with colA:
            if st.button("♻️ Reset ALL votes (keep events)"):
                db.reset_all_votes()
                st.success("All votes have been reset.")
                st.rerun()
        with colB:
            if st.button("🔥 Reset EVERYTHING (events + votes + photos)"):
                db.reset_everything()
                st.success("Database fully reset.")
                st.rerun()

    # --- Export ---
    with tab_export:
        st.write("Download the current leaderboard as a CSV file.")
        export_df = board[["position", "title", "author", "event_date", "average_rating", "total_votes"]]
        export_df.columns = ["Position", "Title", "Author", "Date", "Average Rating", "Total Votes"]
        csv = export_df.to_csv(index=False).encode("utf-8")
        st.download_button(
            "📤 Download results.csv",
            data=csv,
            file_name="alpe_games_results.csv",
            mime="text/csv",
            use_container_width=True,
        )
        st.dataframe(export_df, use_container_width=True, hide_index=True)


# ----------------------------------------------------------------------
# ROUTER
# ----------------------------------------------------------------------
page = st.session_state.page

if page == "🏠 Home":
    page_home()
elif page == "➕ Add Event":
    page_add_event()
elif page == "🖼️ Gallery":
    page_gallery()
elif page == "Event Detail":
    if st.session_state.selected_event:
        page_event_detail(st.session_state.selected_event)
    else:
        st.session_state.page = "🖼️ Gallery"
        st.rerun()
elif page == "🏆 Leaderboard":
    page_leaderboard()
elif page == "📊 Statistics":
    page_statistics()
elif page == "🛠️ Admin":
    page_admin()
