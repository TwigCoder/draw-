import streamlit as st
from dataclasses import dataclass
import time
from typing import List, Dict, Optional
import base64
from io import BytesIO
import json
from pydub import AudioSegment
import threading


@dataclass
class AudioTrack:
    name: str
    mood: str
    file_path: str


@dataclass
class DrawingChallenge:
    prompt: str
    duration: int
    required_elements: List[str]
    difficulty: str


class AudioManager:
    def __init__(self):
        self.tracks = {
            "Calm": [
                AudioTrack("Peaceful Piano", "calm", "audio/peaceful_piano.mp3"),
                AudioTrack("Ocean Waves", "calm", "audio/ocean_waves.mp3"),
            ],
            "Energetic": [
                AudioTrack("Upbeat Rhythm", "energetic", "audio/upbeat.mp3"),
                AudioTrack("Dance Beats", "energetic", "audio/dance.mp3"),
            ],
            "Focus": [
                AudioTrack("Deep Focus", "focus", "audio/deep_focus.mp3"),
                AudioTrack("Study Time", "focus", "audio/study.mp3"),
            ],
        }

    def render_audio_controls(self):
        st.sidebar.markdown("### 🎵 Music Player")
        mood = st.sidebar.selectbox(
            "Select Mood", options=list(self.tracks.keys()), key="music_mood"
        )

        track = st.sidebar.selectbox(
            "Select Track",
            options=[track.name for track in self.tracks[mood]],
            key="music_track",
        )

        cols = st.sidebar.columns([1, 1, 1])
        play_btn = cols[0].button("▶️", key="play_music")
        stop_btn = cols[2].button("⏹️", key="stop_music")

        volume = st.sidebar.slider("Volume", 0.0, 1.0, 0.5, key="music_volume")

        if play_btn:
            track_file = next(t.file_path for t in self.tracks[mood] if t.name == track)
            threading.Thread(target=self.play_audio, args=(track_file,)).start()

        return {
            "mood": mood,
            "track": track,
            "volume": volume,
            "playing": play_btn,
            "stopped": stop_btn,
        }

    def play_audio(self, file_path):
        try:
            audio = AudioSegment.from_mp3(file_path)

            volume_level = st.session_state.get("music_volume", 0.5)
            audio = audio + (volume_level * 10)

            raw_data = audio.raw_data

        except Exception as e:
            st.sidebar.error(f"Error playing audio: {e}")


class SocialFeatures:
    def __init__(self):
        if "drawings" not in st.session_state:
            st.session_state.drawings = []
        if "likes" not in st.session_state:
            st.session_state.likes = {}
        if "active_challenge" not in st.session_state:
            st.session_state.active_challenge = None

    def save_drawing(self, canvas_data, username: str):
        if canvas_data is not None and canvas_data.json_data is not None:
            drawing_data = {
                "id": len(st.session_state.drawings),
                "username": username,
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                "canvas_data": canvas_data.json_data,
                "likes": 0,
                "comments": [],
            }
            st.session_state.drawings.append(drawing_data)
            return True
        return False

    def render_gallery(self):
        st.sidebar.markdown("### 🖼️ Drawing Gallery")

        if len(st.session_state.drawings) == 0:
            st.sidebar.info("No drawings saved yet!")
            return

        selected_drawing = st.sidebar.selectbox(
            "View Drawings",
            options=range(len(st.session_state.drawings)),
            format_func=lambda x: f"{st.session_state.drawings[x]['username']} - {st.session_state.drawings[x]['timestamp']}",
        )

        drawing = st.session_state.drawings[selected_drawing]

        cols = st.sidebar.columns([1, 1])
        if cols[0].button("👍", key=f"like_{selected_drawing}"):
            drawing["likes"] += 1

        cols[1].write(f"{drawing['likes']} likes")

        comment = st.sidebar.text_input(
            "Add comment", key=f"comment_{selected_drawing}"
        )
        if st.sidebar.button("Send", key=f"send_comment_{selected_drawing}"):
            if comment.strip():
                drawing["comments"].append(
                    {
                        "username": st.session_state.username,
                        "text": comment,
                        "timestamp": time.strftime("%H:%M:%S"),
                    }
                )

        if drawing["comments"]:
            st.sidebar.markdown("#### Comments")
            for comment in drawing["comments"]:
                st.sidebar.text(f"{comment['username']}: {comment['text']}")


class ChallengeManager:
    def __init__(self):
        self.challenges = [
            DrawingChallenge(
                "Draw a magical forest",
                300,
                ["trees", "magical elements", "creatures"],
                "Medium",
            ),
            DrawingChallenge(
                "Create an underwater scene", 240, ["fish", "coral", "bubbles"], "Easy"
            ),
            DrawingChallenge(
                "Design a futuristic city",
                360,
                ["buildings", "vehicles", "technology"],
                "Hard",
            ),
        ]

    def render_challenge_controls(self):
        st.sidebar.markdown("### 🎯 Drawing Challenges")

        if st.session_state.active_challenge is None:
            challenge = st.sidebar.selectbox(
                "Select Challenge",
                options=self.challenges,
                format_func=lambda x: f"{x.prompt} ({x.difficulty})",
            )

            if st.sidebar.button("Start Challenge"):
                st.session_state.active_challenge = {
                    "challenge": challenge,
                    "start_time": time.time(),
                }
        else:
            challenge_data = st.session_state.active_challenge
            elapsed = int(time.time() - challenge_data["start_time"])
            remaining = max(0, challenge_data["challenge"].duration - elapsed)

            st.sidebar.markdown(
                f"**Current Challenge:** {challenge_data['challenge'].prompt}"
            )
            st.sidebar.markdown(f"Time Remaining: {remaining//60}:{remaining%60:02d}")

            if remaining == 0:
                st.sidebar.success("Challenge Complete!")
                if st.sidebar.button("Start New Challenge"):
                    st.session_state.active_challenge = None

            required = ", ".join(challenge_data["challenge"].required_elements)
            st.sidebar.markdown(f"Required Elements: {required}")


def setup_audio_styles():
    st.markdown(
        """
        <style>
            .audio-controls {
                display: flex;
                justify-content: space-between;
                align-items: center;
                margin: 10px 0;
            }
            .audio-button {
                width: 40px !important;
                height: 40px !important;
                padding: 0 !important;
                border-radius: 50% !important;
            }
        </style>
    """,
        unsafe_allow_html=True,
    )


def initialize_feature_state():
    if "audio_manager" not in st.session_state:
        st.session_state.audio_manager = AudioManager()
    if "social_features" not in st.session_state:
        st.session_state.social_features = SocialFeatures()
    if "challenge_manager" not in st.session_state:
        st.session_state.challenge_manager = ChallengeManager()


def render_features(canvas_result):
    setup_audio_styles()

    audio_state = st.session_state.audio_manager.render_audio_controls()

    st.session_state.social_features.render_gallery()

    st.session_state.challenge_manager.render_challenge_controls()

    if st.sidebar.button("Save Drawing", key="save_drawing"):
        if st.session_state.social_features.save_drawing(
            canvas_result, st.session_state.username
        ):
            st.sidebar.success("Drawing saved!")
        else:
            st.sidebar.error(
                "Unable to save drawing. Make sure you've drawn something!"
            )
