import os
os.environ["CUDA_VISIBLE_DEVICES"] = "-1"

import numpy as np
import json
import joblib
from tensorflow.keras.models import load_model

# Load model and assets
model = load_model("keras_model.h5")
vectorizer = joblib.load("vectorizer.joblib")

with open("responses.json", "r") as f:
    responses = json.load(f)

# Prompt and inference
prompt = input("Ask a question: ")
X_input = vectorizer.transform([prompt]).toarray()
prediction = model.predict(X_input)
predicted_label = np.argmax(prediction)

print("Response:", responses[predicted_label])
