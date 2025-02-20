import json
import streamlit as st
from datetime import datetime


def normalize_timestamp(timestamp):
    try:
        # Replace a trailing "Z" with "+00:00" for UTC if present
        timestamp = timestamp.replace("Z", "+00:00")
        if "." in timestamp:
            # Separate the main part and the timezone part
            if '+' in timestamp:
                main_part, tz_part = timestamp.split('+', 1)
                tz_part = '+' + tz_part
            elif '-' in timestamp[19:]:
                main_part, tz_part = timestamp.split('-', 1)
                tz_part = '-' + tz_part
            else:
                main_part, tz_part = timestamp, ''
            if '.' in main_part:
                date_part, frac = main_part.split('.', 1)
                # If the fractional part (milliseconds) is less than 3 digits, pad it.
                if len(frac) < 3:
                    frac = frac.ljust(3, '0')
                main_part = f"{date_part}.{frac}"
            timestamp = main_part + tz_part
        return datetime.fromisoformat(timestamp)
    except ValueError:
        return None


st.title("Discord JSON Message Filter")

uploaded_file = st.file_uploader("Upload a Discord JSON file", type=["json"])

if uploaded_file is not None:
    data = json.load(uploaded_file)
    messages = data.get("messages", [])
    st.write(f"Loaded {len(messages)} messages.")

    st.sidebar.header("Filter Options")

    # Date range filter
    start_date = st.sidebar.date_input("Start date", value=datetime(2023, 10, 20))
    end_date = st.sidebar.date_input("End date", value=datetime(2023, 10, 21))

    # Message type filter: get all unique types from messages
    types = sorted(list({msg.get("type", "Unknown") for msg in messages}))
    selected_type = st.sidebar.selectbox("Message Type", options=["All"] + types)

    # Author name filter
    author_filter = st.sidebar.text_input("Author Name contains")

    # message content filter
    message_filter = st.sidebar.text_input("Message contains")

    # Reaction filter (by emoji name)
    reaction_filter = st.sidebar.text_input("Reaction Emoji (e.g., thumbsup)")


    def message_matches(msg):
        ts_str = msg.get("timestamp")
        if ts_str:
            ts = normalize_timestamp(ts_str)
            if ts is None:
                return False
            if ts.date() < start_date or ts.date() > end_date:
                return False
        # Filter by message type
        if selected_type != "All" and msg.get("type") != selected_type:
            return False
        # Filter by author name substring
        if author_filter:
            author_name = msg.get("author", {}).get("name", "").lower()
            if author_filter.lower() not in author_name:
                return False
        if message_filter:
            content = msg.get("content").lower()
            if message_filter.lower() not in content:
                return False
        # Filter by reaction emoji substring
        if reaction_filter:
            reactions = msg.get("reactions", [])
            found = False
            for react in reactions:
                emoji_name = react.get("emoji", {}).get("name", "").lower()
                if reaction_filter.lower() in emoji_name:
                    found = True
                    break
            if not found:
                return False
        return True


    filtered_messages = [msg for msg in messages if message_matches(msg)]
    st.write(f"Found {len(filtered_messages)} messages matching filters.")

    # Display filtered messages (author, timestamp, and content)
    for msg in filtered_messages:
        author = msg.get("author", {}).get("name", "Unknown")
        content = msg.get("content", "")
        timestamp = msg.get("timestamp", "")
        st.markdown(f"**{author}** ({timestamp}): {content}")
