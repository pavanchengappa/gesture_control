import cv2
import numpy as np
import platform
import mediapipe as mp
import time

# Platform-specific mouse control
if platform.system() == 'Windows':
    import win32api
    import win32con
    
    def move_mouse(x, y):
        win32api.SetCursorPos((int(x), int(y)))
    
    def click(button='left'):
        if button == 'left':
            win32api.mouse_event(win32con.MOUSEEVENTF_LEFTDOWN, 0, 0)
            win32api.mouse_event(win32con.MOUSEEVENTF_LEFTUP, 0, 0)
        elif button == 'right':
            win32api.mouse_event(win32con.MOUSEEVENTF_RIGHTDOWN, 0, 0)
            win32api.mouse_event(win32con.MOUSEEVENTF_RIGHTUP, 0, 0)
else:
    def move_mouse(x, y):
        print("Mouse control not supported on this platform")
    
    def click(button='left'):
        print("Clicking not supported on this platform")

class AdvancedHandGestureControl:
    def __init__(self, debug=True):
        # Debug flag
        self.debug = debug
        
        # MediaPipe Hand Tracking
        self.mp_hands = mp.solutions.hands
        self.hands = self.mp_hands.Hands(
            static_image_mode=False,
            max_num_hands=1,
            min_detection_confidence=0.5,  # Lowered for better detection
            min_tracking_confidence=0.5
        )
        self.mp_drawing = mp.solutions.drawing_utils
        
        # Screen dimensions
        self.screen_width, self.screen_height = 1920, 1080
        
        # Gesture state tracking
        self.last_gesture_time = time.time()
        self.gesture_cooldown = 0.5  # seconds between gestures

    def calculate_distance(self, p1, p2):
        """Calculate Euclidean distance between two landmarks"""
        return np.sqrt((p1.x - p2.x)**2 + (p1.y - p2.y)**2)

    def log(self, message):
        """Debug logging"""
        if self.debug:
            print(message)

    def detect_finger_state(self, hand_landmarks):
        """Detect which fingers are up"""
        # Finger tip and MCP (metacarpophalangeal) landmarks
        finger_tips = [
            self.mp_hands.HandLandmark.THUMB_TIP,
            self.mp_hands.HandLandmark.INDEX_FINGER_TIP,
            self.mp_hands.HandLandmark.MIDDLE_FINGER_TIP,
            self.mp_hands.HandLandmark.RING_FINGER_TIP,
            self.mp_hands.HandLandmark.PINKY_TIP
        ]
        finger_mcps = [
            self.mp_hands.HandLandmark.THUMB_MCP,
            self.mp_hands.HandLandmark.INDEX_FINGER_MCP,
            self.mp_hands.HandLandmark.MIDDLE_FINGER_MCP,
            self.mp_hands.HandLandmark.RING_FINGER_MCP,
            self.mp_hands.HandLandmark.PINKY_MCP
        ]
        
        # Check if fingertip is above MCP
        finger_states = [
            hand_landmarks.landmark[tip].y < hand_landmarks.landmark[mcp].y
            for tip, mcp in zip(finger_tips, finger_mcps)
        ]
        
        return finger_states

    def control_mouse(self):
        video_capture = cv2.VideoCapture(0)
        
        while True:
            ret, frame = video_capture.read()
            if not ret:
                break
            
            # Mirror image
            frame = cv2.flip(frame, 1)
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            
            # Hand detection
            results = self.hands.process(rgb_frame)
            
            if results.multi_hand_landmarks:
                for hand_landmarks in results.multi_hand_landmarks:
                    # Draw landmarks
                    self.mp_drawing.draw_landmarks(
                        frame, hand_landmarks, self.mp_hands.HAND_CONNECTIONS)
                    
                    # Detect finger states
                    finger_states = self.detect_finger_state(hand_landmarks)
                    
                    # Get hand center coordinates
                    wrist = hand_landmarks.landmark[self.mp_hands.HandLandmark.WRIST]
                    screen_x = int(wrist.x * self.screen_width)
                    screen_y = int(wrist.y * self.screen_height)
                    
                    # Current time for gesture control
                    current_time = time.time()
                    
                    # Single index finger
                    if finger_states[1] and not finger_states[2]:
                        # Move cursor
                        move_mouse(screen_x, screen_y)
                        
                        # Quick click detection
                        if current_time - self.last_gesture_time > self.gesture_cooldown:
                            self.log("Left Click Detected")
                            click('left')
                            self.last_gesture_time = current_time
                    
                    # Single middle finger
                    elif finger_states[2] and not finger_states[1]:
                        if current_time - self.last_gesture_time > self.gesture_cooldown:
                            self.log("Right Click Detected")
                            click('right')
                            self.last_gesture_time = current_time
                    
                    # Both index and middle fingers
                    elif finger_states[1] and finger_states[2]:
                        # Smooth cursor movement
                        move_mouse(screen_x, screen_y)
                        self.log("Two Finger Cursor Movement")
            
            # Display frame
            cv2.imshow('Hand Gesture Mouse Control', frame)
            
            # Exit on 'q'
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
        
        video_capture.release()
        cv2.destroyAllWindows()

def main():
    controller = AdvancedHandGestureControl()
    controller.control_mouse()

if __name__ == "__main__":
    main()