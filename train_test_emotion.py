import pandas as pd
import numpy as np
from sklearn.preprocessing import LabelEncoder
from sklearn.model_selection import train_test_split
from tensorflow.keras.preprocessing.text import Tokenizer
from tensorflow.keras.preprocessing.sequence import pad_sequences
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Embedding, LSTM, Dense, Dropout

# Load dataset
df = pd.read_csv("emotion.csv")   # columns: text, emotion

texts = df["text"].values
labels = df["emotion"].values

# Encode labels
le = LabelEncoder()
labels_encoded = le.fit_transform(labels)

# Tokenize text
tokenizer = Tokenizer(num_words=10000)
tokenizer.fit_on_texts(texts)

sequences = tokenizer.texts_to_sequences(texts)
padded = pad_sequences(sequences, maxlen=100)

# Train-test split
X_train, X_test, y_train, y_test = train_test_split(
    padded, labels_encoded, test_size=0.2, random_state=42
)

# Build LSTM model
model = Sequential([
    Embedding(10000, 128, input_length=100),
    LSTM(128, return_sequences=False),
    Dropout(0.5),
    Dense(64, activation="relu"),
    Dense(len(le.classes_), activation="softmax")
])

model.compile(
    loss="sparse_categorical_crossentropy",
    optimizer="adam",
    metrics=["accuracy"]
)

# Train
model.fit(X_train, y_train, epochs=5, batch_size=64, validation_split=0.1)

# Save model & tokenizer
model.save("text_emotion_model.h5")

import pickle
pickle.dump(tokenizer, open("tokenizer.pkl", "wb"))
pickle.dump(le, open("label_encoder.pkl", "wb"))

print("✅ Text Emotion Model Saved")
