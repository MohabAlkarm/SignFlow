import cv2
import os
import mediapipe as mp
import numpy as np
import pandas as pd
import logging
import asyncio
import tensorflow as tf
from agora_rtm_sender import send_rtm_message, generate_rtm_token

def extract_landmarks(results):
    def get_landmarks(landmark_list, expected_len):
        if landmark_list:
            return np.array([[l.x, l.y, l.z] for l in landmark_list.landmark]).flatten()
        else:
            return np.zeros(expected_len * 3)

    pose = get_landmarks(results.pose_landmarks, 33)
    left = get_landmarks(results.left_hand_landmarks, 21)
    right = get_landmarks(results.right_hand_landmarks, 21)

    return np.concatenate([pose, left, right])  # shape: (225,)


def mediapipe_detection(image, model):
    image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB) # COLOR CONVERSION BGR 2 RGB
    image.flags.writeable = False                  # Image is no longer writeable
    results = model.process(image)                 # Make prediction
    image.flags.writeable = True                   # Image is now writeable
    image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR) # COLOR COVERSION RGB 2 BGR
    return image, results


path = os.path.abspath(os.path.join(os.getcwd(), "base", "action.h5"));
model = tf.keras.models.load_model(path)

mp_holistic = mp.solutions.holistic
mp_drawing = mp.solutions.drawing_utils
holistic = mp_holistic.Holistic(static_image_mode=False)

path = os.path.abspath(os.path.join(os.getcwd(), "base", "KARSL-190_Labels.xlsx"));
karsl_df = pd.read_excel(path)
actions = []

generate_rtm_token()

for ix, row in karsl_df.iterrows():
    actions.append(row['Sign-Arabic'])

cap = cv2.VideoCapture(0)

async def gesture_recognition_loop():
  
  sequence = []
  sentence = []
  predictions = []
  threshold = 0.5 / 190
  

  with mp_holistic.Holistic(min_detection_confidence=0.5, min_tracking_confidence=0.5) as holistic:
      while cap.isOpened():

          # Read feed
          ret, frame = cap.read()
          # Make detections
          frame.flags.writeable = False
          frame, results = mediapipe_detection(frame, holistic)

          # 2. Prediction logic
          keypoints = extract_landmarks(results)
          sequence.append(keypoints)
          sequence = sequence[-30:]

          if (results.right_hand_landmarks or results.left_hand_landmarks) and len(sequence) == 30:
              res = model.predict(np.expand_dims(sequence, axis=0))[0]
              predicted_word = str(actions[np.argmax(res)])
              
              # await broadcast_translation(predicted_word)
              send_rtm_message("listener1", predicted_word)
              predictions.append(np.argmax(res))
              sequence = []
              
          # Break 
          if cv2.waitKey(10) & 0xFF == ord('q'):
              break
      cap.release()
      cv2.destroyAllWindows()
      
async def main():
  await gesture_recognition_loop()

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())