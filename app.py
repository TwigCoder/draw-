import streamlit as st

st.set_page_config(page_title="Draw!", layout="wide")

from streamlit_drawable_canvas import st_canvas
from datetime import datetime
import simpleaudio as sa
import threading
import time
import random
import numpy as np
import sqlite3
import cv2


class ColorPalette:
    def __init__(self):
        self.palettes = {
            "Basic": ["#000000", "#FFFFFF", "#FF0000", "#00FF00", "#0000FF"],
            "Pastel": ["#FFB3BA", "#BAFFC9", "#BAE1FF", "#FFFFBA", "#FFB3FF"],
            "Earth": ["#4B371C", "#7A542E", "#8B7355", "#A67B5B", "#C4A484"],
            "Ocean": ["#00204A", "#005792", "#00BBF0", "#00B2CA", "#89CFF0"],
        }


def initialize_session_state():
    if "color_palette" not in st.session_state:
        st.session_state.color_palette = ColorPalette()
    if "current_color" not in st.session_state:
        st.session_state.current_color = "#000000"
    if "canvas_width" not in st.session_state:
        st.session_state.canvas_width = 1400
    if "canvas_height" not in st.session_state:
        st.session_state.canvas_height = 800


def initialize_database():
    conn = sqlite3.connect("chat.db")
    cursor = conn.cursor()
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS chat (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT,
            message TEXT,
            timestamp TEXT
        )
        """
    )
    conn.commit()
    conn.close()


def save_message(username, message):
    conn = sqlite3.connect("chat.db")
    cursor = conn.cursor()
    timestamp = datetime.now().strftime("%H:%M:%S")
    cursor.execute(
        "INSERT INTO chat (username, message, timestamp) VALUES (?, ?, ?)",
        (username, message, timestamp),
    )
    conn.commit()
    conn.close()


def load_messages():
    conn = sqlite3.connect("chat.db")
    cursor = conn.cursor()
    cursor.execute("SELECT username, message, timestamp FROM chat ORDER BY id DESC")
    messages = cursor.fetchall()
    conn.close()
    return messages


def render_toolbar():
    st.sidebar.title("Drawing Tools")

    drawing_mode = st.sidebar.selectbox(
        "Drawing Tool",
        ("freedraw", "line", "rect", "circle", "polygon", "transform"),
        key="drawing_mode",
    )

    stroke_width = st.sidebar.slider("Stroke Width", 1, 25, 3, key="stroke_width")

    st.sidebar.markdown("### Color Palettes")
    palette_name = st.sidebar.selectbox(
        "Select Palette",
        list(st.session_state.color_palette.palettes.keys()),
        key="palette_select",
    )

    colors = st.session_state.color_palette.palettes[palette_name]
    cols = st.sidebar.columns(5)
    for i, color in enumerate(colors):
        if cols[i % 5].button(
            "⬤",
            key=f"color_button_{palette_name}_{i}",
            help=color,
            type="secondary",
        ):
            st.session_state.current_color = color

    custom_color = st.sidebar.color_picker(
        "Custom Color", st.session_state.current_color, key="custom_color"
    )
    if custom_color != st.session_state.current_color:
        st.session_state.current_color = custom_color

    st.sidebar.markdown("---")
    st.sidebar.markdown("### Resize Canvas")
    st.sidebar.markdown(
        "Note: This is currently misbehaving and will be fixed once I figure out the issue."
    )
    new_width = st.sidebar.number_input(
        "Width",
        value=st.session_state.canvas_width,
        min_value=100,
        max_value=5000,
        step=10,
    )
    new_height = st.sidebar.number_input(
        "Height",
        value=st.session_state.canvas_height,
        min_value=100,
        max_value=5000,
        step=10,
    )

    if st.sidebar.button("Resize Canvas"):
        resize_canvas(new_width, new_height)

    return drawing_mode, stroke_width, st.session_state.current_color


def resize_canvas(new_width, new_height):
    if "canvas_image" in st.session_state and st.session_state.canvas_image is not None:

        scale_x = new_width / st.session_state.canvas_width
        scale_y = new_height / st.session_state.canvas_height
        scale_factor = min(scale_x, scale_y)

        resized_image = cv2.resize(
            st.session_state.canvas_image,
            (
                int(st.session_state.canvas_image.shape[1] * scale_factor),
                int(st.session_state.canvas_image.shape[0] * scale_factor),
            ),
            interpolation=cv2.INTER_LINEAR,
        )

        st.session_state.canvas_image = resized_image

    st.session_state.canvas_width = new_width
    st.session_state.canvas_height = new_height


def render_chat():
    st.sidebar.markdown("---")
    st.sidebar.title("Chat & Notes")

    username = st.sidebar.text_input("Your name", key="username")
    message = st.sidebar.text_area("Message", key="message")

    if st.sidebar.button("Send", key="send_button") and username and message:
        save_message(username, message)

    chat_container = st.sidebar.container()
    with chat_container:
        messages = load_messages()
        for username, message, timestamp in messages:
            st.text(f"[{timestamp}] {username}: {message}")


def render_canvas(drawing_mode, stroke_width, stroke_color):
    if "canvas_image" not in st.session_state:
        st.session_state.canvas_image = None

    canvas_result = st_canvas(
        fill_color="rgba(255, 165, 0, 0.3)",
        stroke_width=stroke_width,
        stroke_color=stroke_color,
        background_color="#ffffff",
        width=st.session_state.canvas_width,
        height=st.session_state.canvas_height,
        drawing_mode=drawing_mode,
        key="canvas",
    )

    if canvas_result and canvas_result.image_data is not None:
        st.session_state.canvas_image = canvas_result.image_data

    if canvas_result and drawing_mode in ["freedraw", "line", "rect"]:
        generate_chime(frequency=600, duration=150)
    elif drawing_mode == "transform":
        generate_chime(frequency=300, duration=150)

    return canvas_result


def setup_styles():
    st.markdown(
        """
        <style>
            .stApp {
                max-width: 100%;
            }
            section.main > div {
                max-width: 100%;
                padding: 0;
            }
            div[data-testid="stSidebarContent"] {
                padding: 1rem;
            }
            canvas {
                cursor: crosshair;
            }
            .stButton>button {
                width: 100%;
                height: 30px;
                padding: 0 !important;
                font-size: 20px !important;
                line-height: 1 !important;
            }
        </style>
    """,
        unsafe_allow_html=True,
    )


def generate_chime(frequency=440, duration=200):
    pass


def initialize_music_controls():
    if "is_music_playing" not in st.session_state:
        st.session_state.is_music_playing = False
    if "music_mood" not in st.session_state:
        st.session_state.music_mood = "happy"


def main():
    initialize_session_state()
    initialize_database()
    initialize_music_controls()
    setup_styles()

    drawing_mode, stroke_width, stroke_color = render_toolbar()
    render_chat()
    render_canvas(drawing_mode, stroke_width, stroke_color)


if __name__ == "__main__":
    main()
