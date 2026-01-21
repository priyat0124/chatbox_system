# ----------------------------
# IMPORTS
# ----------------------------
import streamlit as st
from textblob import TextBlob
import pandas as pd
from st_audiorec import st_audiorec
import tempfile
import os
from gtts import gTTS
import speech_recognition as sr
import random

from streamlit_webrtc import webrtc_streamer, VideoTransformerBase
import cv2
import av


st.markdown("""
<style>

/* 🌈 Animated Gradient Background */
body {
    background: linear-gradient(-45deg, #89f7fe, #66a6ff, #fbc2eb, #a6c1ee);
    background-size: 400% 400%;
    animation: gradientBG 15s ease infinite;
}

@keyframes gradientBG {
    0% { background-position: 0% 50%; }
    50% { background-position: 100% 50%; }
    100% { background-position: 0% 50%; }
}

/* 🧠 Title Glow Animation */
h1 {
    text-align: center;
    font-size: 3em;
    color: #2c2c2c;
    animation: glow 2s ease-in-out infinite alternate;
}

@keyframes glow {
    from {
        text-shadow: 0 0 5px #fff;
    }
    to {
        text-shadow: 0 0 20px #ff8fd4, 0 0 30px #66a6ff;
    }
}

/* 💬 Chat Bubbles */
.user-bubble {
    background: linear-gradient(135deg, #43cea2, #185a9d);
    color: white;
    padding: 14px 18px;
    border-radius: 22px;
    margin: 12px;
    text-align: right;
    font-weight: 500;
    animation: slideRight 0.4s ease;
}

.bot-bubble {
    background: linear-gradient(135deg, #fdfbfb, #ebedee);
    color: #333;
    padding: 14px 18px;
    border-radius: 22px;
    margin: 12px;
    animation: slideLeft 0.4s ease;
}

/* 🎞️ Chat Animation */
@keyframes slideRight {
    from { transform: translateX(50px); opacity: 0; }
    to { transform: translateX(0); opacity: 1; }
}

@keyframes slideLeft {
    from { transform: translateX(-50px); opacity: 0; }
    to { transform: translateX(0); opacity: 1; }
}

/* 🎛️ Buttons Animation */
button {
    background: linear-gradient(135deg, #ff758c, #ff7eb3) !important;
    color: white !important;
    border-radius: 30px !important;
    padding: 8px 20px !important;
    font-weight: bold !important;
    transition: transform 0.2s ease, box-shadow 0.2s ease;
}

button:hover {
    transform: scale(1.08);
    box-shadow: 0 6px 15px rgba(0,0,0,0.25);
}

/* 📈 Chart Container Glow */
div[data-testid="stLineChart"] {
    background: white;
    border-radius: 20px;
    padding: 10px;
    box-shadow: 0 0 20px rgba(0,0,0,0.15);
    animation: fadeIn 1s ease-in;
}

@keyframes fadeIn {
    from { opacity: 0; }
    to { opacity: 1; }
}

/* 📚 Sidebar Styling */
section[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #fbc2eb, #a6c1ee);
    padding: 20px;
}

/* ✨ Sidebar Quote Card */
.stAlert {
    border-radius: 15px !important;
    animation: pulse 2s infinite;
}

@keyframes pulse {
    0% { box-shadow: 0 0 0 0 rgba(255,126,179,0.5); }
    70% { box-shadow: 0 0 0 15px rgba(255,126,179,0); }
    100% { box-shadow: 0 0 0 0 rgba(255,126,179,0); }
}

</style>
""", unsafe_allow_html=True)


# ----------------------------
# FIX: SENTIMENT → EMOTION MAPPING
# ----------------------------
def sentiment_to_emotion(polarity):
    if polarity > 0.4:
        return "Happy"
    elif polarity > 0.05:
        return "Neutral"
    elif polarity > -0.3:
        return "Sad"
    else:
        return "Angry"

# ----------------------------
# VIDEO EMOTION ADVICE (RICH RESPONSES)
# ----------------------------
VIDEO_EMOTION_ADVICE = {
    "Happy": [
        "You seem genuinely happy 😊 That’s wonderful to see.",
        "Try to fully enjoy this moment — happiness grows when noticed 🌟",
        "Sharing your joy with someone can make it even stronger ❤️",
        "Take a mental note of what caused this feeling 📝",
        "You deserve moments like this — let yourself smile freely 🌈",
        "Use this positive energy to do something meaningful today 🚀",
        "Practicing gratitude can help this feeling last longer 🙏"
    ],

    "Neutral": [
        "You appear calm and balanced 😌 That’s perfectly okay.",
        "Not every moment needs strong emotions — neutrality can be restful 🤍",
        "This is a good time for gentle reflection 🧠",
        "Try slow breathing and notice how your body feels 🧘",
        "Doing something simple you enjoy may help lift your mood 🌱",
        "Stability is also a form of strength 💪",
        "Check in with yourself: *What do I need right now?*"
    ],

    "Sad": [
        "I notice signs of sadness 😔 I’m really glad you’re here.",
        "It’s okay to feel this way — your emotions are valid 💙",
        "You don’t have to go through this alone 🤝",
        "Try taking a slow, deep breath — you’re safe right now 🌬️",
        "Reaching out to someone you trust may help 📞",
        "Be gentle with yourself — healing takes time 🤍",
        "This feeling will not last forever 🌈"
    ],

    "Angry": [
        "I sense tension or anger 😠 That can feel overwhelming.",
        "Strong emotions often mean something important needs attention 🧠",
        "Let’s slow things down together — take a deep breath 🌬️",
        "Relax your shoulders and unclench your jaw 🧘",
        "Stepping away for a moment may help 🌿",
        "It’s okay to feel angry — you still deserve calm 💙",
        "You’re allowed to pause before reacting 🤍"
    ],

    "Surprise": [
        "That expression suggests surprise 😮",
        "Unexpected moments can bring mixed emotions 🌱",
        "Take a moment to understand what you’re feeling 🧠",
        "If it feels overwhelming, try grounding yourself 🌬️",
        "You’re doing well by checking in 💙"
    ]
}



##################
# ----------------------------
# EXTRA: TAMIL MOTIVATIONAL SONGS (AUDIO)
# ----------------------------
TAMIL_MOTIVATIONAL_SONGS = {
    "Very Positive": [
        "https://www.soundhelix.com/examples/mp3/SoundHelix-Song-1.mp3"
    ],
    "Positive": [
        "https://www.soundhelix.com/examples/mp3/SoundHelix-Song-2.mp3"
    ],
    "Neutral": [
        "https://www.soundhelix.com/examples/mp3/SoundHelix-Song-3.mp3"
    ],
    "Negative": [
        "https://www.soundhelix.com/examples/mp3/SoundHelix-Song-4.mp3"
    ],
    "Very Negative": [
        "https://www.soundhelix.com/examples/mp3/SoundHelix-Song-5.mp3"
    ]
}

# ----------------------------
# EXTRA: TAMIL MOTIVATIONAL VIDEO SONGS (VIDEO CHAT)
# ----------------------------
TAMIL_MOTIVATIONAL_VIDEOS = {
    "Happy": [
        "https://www.youtube.com/embed/2Vv-BfVoq4g"
    ],
    "Neutral": [
        "https://www.youtube.com/embed/l482T0yNkeo"
    ],
    "Sad": [
        "https://www.youtube.com/embed/hLQl3WQQoQ0"
    ],
    "Angry": [
        "https://www.youtube.com/embed/fLexgOxsZu0"
    ]
}

# ----------------------------
# HELPER FUNCTIONS
# ----------------------------
def analyze_sentiment(text):
    polarity = TextBlob(text).sentiment.polarity
    if polarity > 0.5:
        return "Very Positive", polarity
    elif polarity > 0.1:
        return "Positive", polarity
    elif polarity >= -0.1:
        return "Neutral", polarity
    elif polarity > -0.5:
        return "Negative", polarity
    else:
        return "Very Negative", polarity


def provide_coping_strategy(sentiment):
    strategies = {
        "Very Positive": [
            "Keep enjoying this positive energy 🌟",
            "Share your happiness with someone you trust ❤️",
            "Celebrate even small wins 🎉",
            "Write down what made you feel good 📝"
        ],
        "Positive": [
            "Practice gratitude 🙌",
            "Listen to uplifting music 🎶",
            "Do something creative 🎨",
            "Spend time in nature 🌿"
        ],
        "Neutral": [
            "Take a calm walk 🚶",
            "Practice mindful breathing 🧘",
            "Drink water and relax 💧",
            "Do a simple activity you enjoy 🎮"
        ],
        "Negative": [
            "Take slow deep breaths 🌬️",
            "Reach out to someone you trust 👥",
            "Listen to calming sounds 🎧",
            "Be gentle with yourself 🤍"
        ],
        "Very Negative": [
            "I’m really sorry you’re feeling this way 💔",
            "You don’t have to face this alone 🤝",
            "Please reach out to a trusted person 📞",
            "If you feel unsafe, contact emergency services 🚨"
        ]
    }
    return strategies.get(sentiment, ["Take care of yourself 💚"])


def generate_video_response(emotion):
    advice = VIDEO_EMOTION_ADVICE.get(emotion, ["I’m here with you 💚"])
    selected = random.sample(advice, min(4, len(advice)))
    return " ".join(selected)


def text_to_speech(text):
    try:
        tts = gTTS(text, lang="en")
        tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".mp3")
        tmp.close()
        tts.save(tmp.name)
        return tmp.name
    except:
        return None


def speech_to_text(path):
    r = sr.Recognizer()
    try:
        with sr.AudioFile(path) as source:
            audio = r.record(source)
            return r.recognize_google(audio)
    except:
        return None


def generate_response(sentiment, persona):
    base = {
        "Very Positive": "That’s wonderful to hear!",
        "Positive": "That sounds encouraging.",
        "Neutral": "Thanks for sharing.",
        "Negative": "That sounds really tough.",
        "Very Negative": "I’m truly sorry you’re feeling this way."
    }

    encouragements = [
        "You’re doing your best 💙",
        "Small steps still matter 🌱",
        "Be kind to yourself 🤍",
        "You’re stronger than you think ✨"
    ]

    tips = provide_coping_strategy(sentiment)

    return f"""{base[sentiment]} ({persona})

💬 {random.choice(encouragements)}

💡 Suggested Coping Strategies:
- """ + "\n- ".join(tips)


# ----------------------------
# VIDEO PROCESSOR
# ----------------------------
class VideoProcessor(VideoTransformerBase):
    def __init__(self):
        self.last_emotion = "Neutral"

    def transform(self, frame):
        img = frame.to_ndarray(format="bgr24")
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

        face_cascade = cv2.CascadeClassifier(
            cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
        )

        faces = face_cascade.detectMultiScale(gray, 1.3, 5)

        if len(faces) > 0:
            self.last_emotion = "Face Detected"
            

        for (x, y, w, h) in faces:
            cv2.rectangle(img, (x, y), (x+w, y+h), (0, 255, 0), 2)
            cv2.putText(
                img, self.last_emotion, (x, y-10),
                cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 255, 0), 2
            )
        return img


# ----------------------------
# PAGE CONFIG
# ----------------------------
st.set_page_config("AI Health Therapist", "🧠", layout="wide")

# ----------------------------
# SESSION STATE
# ----------------------------
for key in ["messages", "mood_tracker", "video_mood_tracker"]:
    if key not in st.session_state:
        st.session_state[key] = []

if "video_emotion" not in st.session_state:
    st.session_state.video_emotion = "Neutral"
if "video_responded" not in st.session_state:
    st.session_state.video_responded = False

# ----------------------------
# UI
# ----------------------------
st.title("🧠 AI Based Emotional Wellness System")

persona = st.selectbox(
    "Choose Bot Personality",
    ["Gentle Listener", "Friendly Cheerful", "Motivational Coach", "Calm & Reflective"]
)

mode = st.radio(
    "Choose Mode",
    ["💬 Text Chat", "🎙️ Voice Chat", "🎥 Video Chat"]
)


#####################
enable_media = st.checkbox(
    "🎧 Enable Songs / Videos",
    value=True
)

# ----------------------------
# TEXT CHAT
# ----------------------------
if mode == "💬 Text Chat":
    msg = st.text_input("Type your message")

    if st.button("Send") and msg:
        sentiment, pol = analyze_sentiment(msg)
        reply = generate_response(sentiment, persona)

        st.session_state.messages += [("You", msg), ("Therapist", reply)]
        st.session_state.mood_tracker.append(pol)

        # ✅ FIX: Song inside sentiment block
        if enable_media:
            song_list = TAMIL_MOTIVATIONAL_SONGS.get(sentiment, [])
            if song_list:
                st.markdown("### 🎶 Song for You")
                st.audio(random.choice(song_list))


# ----------------------------
# VOICE CHAT
# ----------------------------
elif mode == "🎙️ Voice Chat":
    audio = st_audiorec()

    if audio:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as f:
            f.write(audio)
            path = f.name

        text = speech_to_text(path)
        os.remove(path)

        if text:
            sentiment, pol = analyze_sentiment(text)
            reply = generate_response(sentiment, persona)

            st.session_state.messages += [("You", text), ("Therapist", reply)]
            st.session_state.mood_tracker.append(pol)

            tts = text_to_speech(reply)
            if tts:
                st.audio(tts)

            # ✅ FIX: Song inside sentiment block
            if enable_media:
                song_list = TAMIL_MOTIVATIONAL_SONGS.get(sentiment, [])
                if song_list:
                    st.markdown("### 🎶 Song for You")
                    st.audio(random.choice(song_list))


# ----------------------------
# VIDEO CHAT
# ----------------------------
elif mode == "🎥 Video Chat":

    st.info("📹 Keep your camera ON and speak using the mic below")

    ctx = webrtc_streamer(
        key="video",
        video_processor_factory=VideoProcessor,
        media_stream_constraints={"video": True, "audio": False},
        async_processing=True,
    )

    audio = st_audiorec()

    if audio:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as f:
            f.write(audio)
            audio_path = f.name

        spoken_text = speech_to_text(audio_path)
        os.remove(audio_path)

        if spoken_text:
            # Analyze sentence
            sentiment, polarity = analyze_sentiment(spoken_text)
            emotion = sentiment_to_emotion(polarity)

            # Get advice
            full_reply = "\n\n".join(VIDEO_EMOTION_ADVICE.get(emotion, []))

            # Store chat
            st.session_state.messages += [
                ("You (Video)", spoken_text),
                ("Therapist", f"**Detected Emotion:** {emotion}\n\n{full_reply}")
            ]

            st.session_state.video_mood_tracker.append(
    VIDEO_EMOTION_POLARITY.get(emotion, 0.0)
)

            # 🔊 Voice reply
            tts = text_to_speech(full_reply)
            if tts:
                st.audio(tts)

            # 🎬 EXTRA: Motivational Tamil Video Song
            if enable_media:
                video_list = TAMIL_MOTIVATIONAL_VIDEOS.get(emotion, [])
                if video_list:
                    st.markdown("### 🎬 Video Song")
                    st.markdown(
                        f"""
                        <iframe width="100%" height="315"
                        src="{random.choice(video_list)}"
                        frameborder="0"
                        allowfullscreen></iframe>
                        """,
                        unsafe_allow_html=True
                    )

# ----------------------------
# CHAT DISPLAY
# ----------------------------
st.subheader("💬 Chat History")
for s, m in st.session_state.messages:
    cls = "user-bubble" if s.startswith("You") else "bot-bubble"
    st.markdown(f"<div class='{cls}'>{m}</div>", unsafe_allow_html=True)

# ----------------------------
# MOOD TRACKER
# ----------------------------
st.subheader("📈 Mood Tracker (Text + Voice + Video)")
data = st.session_state.mood_tracker + st.session_state.video_mood_tracker
if data:
    st.line_chart(data)

# ----------------------------
# SIDEBAR
# ----------------------------
st.sidebar.title("🌿 Mental Health Support")

st.sidebar.markdown("""
### 📞 Emergency Help
- **Tele MANAS (India):** 14416 / 1-800-891-4416  
- **Crisis Text Line:** Text **HELLO** to 741741  
""")

st.sidebar.markdown("""
### 🔗 Helpful Links
- https://www.who.int/health-topics/mental-health
- https://tncea.dmrhs.tn.gov.in/mental_health.php
- https://nimhans.ac.in/
""")

quotes = [
    "Healing takes time, and that’s okay 🌱",
    "You matter more than you realize 💙",
    "Progress, not perfection ✨",
    "Be gentle with yourself 🤍",
    "Small steps lead to big change 🌈"
]

st.sidebar.success(random.choice(quotes))
