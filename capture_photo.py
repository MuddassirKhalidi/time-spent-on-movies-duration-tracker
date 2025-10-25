#!/usr/bin/env python3
"""
Camera Photo Capture Script
Takes a photo using the default camera and saves it to a specified location.
"""

import cv2
import argparse
import os
import sys
from datetime import datetime

def capture_photo(output_path=None, camera_index=0, show_preview=True):
    """
    Capture a photo from the camera and save it to the specified path.
    
    Args:
        output_path (str): Path where to save the photo. If None, uses timestamp.
        camera_index (int): Camera index (0 for default camera)
        show_preview (bool): Whether to show camera preview before capturing
    
    Returns:
        str: Path to the saved photo, or None if failed
    """
    
    # Initialize camera
    cap = cv2.VideoCapture(camera_index)
    
    if not cap.isOpened():
        print(f"Error: Could not open camera {camera_index}")
        return None
    
    # Set camera properties for better quality
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1920)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 1080)
    cap.set(cv2.CAP_PROP_FPS, 30)
    
    print("Camera initialized successfully!")
    print("Press 'SPACE' to capture photo, 'ESC' to exit")
    
    if show_preview:
        print("Showing camera preview...")
        
        while True:
            ret, frame = cap.read()
            if not ret:
                print("Error: Could not read from camera")
                break
            
            # Add instructions on the frame
            cv2.putText(frame, "Press SPACE to capture, ESC to exit", 
                       (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
            
            cv2.imshow('Camera Preview - Press SPACE to capture', frame)
            
            key = cv2.waitKey(1) & 0xFF
            
            if key == ord(' '):  # Space key pressed
                # Capture the photo
                photo_path = save_photo(frame, output_path)
                if photo_path:
                    print(f"Photo saved successfully: {photo_path}")
                    cv2.putText(frame, "Photo captured!", 
                               (10, 70), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
                    cv2.imshow('Camera Preview - Press SPACE to capture', frame)
                    cv2.waitKey(2000)  # Show "Photo captured!" message for 2 seconds
                break
            elif key == 27:  # ESC key pressed
                print("Capture cancelled")
                break
    
    else:
        # Capture immediately without preview
        ret, frame = cap.read()
        if ret:
            photo_path = save_photo(frame, output_path)
            if photo_path:
                print(f"Photo saved successfully: {photo_path}")
        else:
            print("Error: Could not capture photo")
            photo_path = None
    
    # Cleanup
    cap.release()
    cv2.destroyAllWindows()
    
    return photo_path

def save_photo(frame, output_path=None):
    """
    Save the captured frame to a file.
    
    Args:
        frame: The captured frame from camera
        output_path: Path where to save the photo
    
    Returns:
        str: Path to the saved photo, or None if failed
    """
    
    if output_path is None:
        # Generate filename with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = f"photo_{timestamp}.jpg"
    
    # Ensure the output path has a proper file extension
    if not os.path.splitext(output_path)[1]:
        output_path += '.jpg'
    
    # Ensure the directory exists
    os.makedirs(os.path.dirname(output_path) if os.path.dirname(output_path) else '.', exist_ok=True)
    
    # Save the photo
    success = cv2.imwrite(output_path, frame)
    
    if success:
        return output_path
    else:
        print(f"Error: Could not save photo to {output_path}")
        return None

def list_available_cameras():
    """List all available cameras."""
    print("Checking for available cameras...")
    available_cameras = []
    
    for i in range(10):  # Check first 10 camera indices
        cap = cv2.VideoCapture(i)
        if cap.isOpened():
            available_cameras.append(i)
            cap.release()
    
    if available_cameras:
        print(f"Available cameras: {available_cameras}")
    else:
        print("No cameras found!")
    
    return available_cameras

def main():
    parser = argparse.ArgumentParser(description='Capture a photo using the camera')
    parser.add_argument('-o', '--output', type=str, help='Output path for the photo')
    parser.add_argument('-c', '--camera', type=int, default=0, help='Camera index (default: 0)')
    parser.add_argument('--no-preview', action='store_true', help='Capture immediately without preview')
    parser.add_argument('--list-cameras', action='store_true', help='List available cameras')
    
    args = parser.parse_args()
    
    if args.list_cameras:
        list_available_cameras()
        return
    
    # If output path is provided but no directory specified, save to targets directory
    if args.output and not os.path.dirname(args.output):
        args.output = os.path.join('targets', args.output)
    
    # Capture the photo
    photo_path = capture_photo(
        output_path=args.output,
        camera_index=args.camera,
        show_preview=not args.no_preview
    )
    
    if photo_path:
        print(f"\n✅ Photo captured successfully!")
        print(f"📁 Saved to: {os.path.abspath(photo_path)}")
        
        # If saved to targets directory, show usage example
        if 'targets' in photo_path:
            filename = os.path.basename(photo_path)
            print(f"\n💡 You can now use this photo with the demo:")
            print(f"   python3 demo.py --name \"Person Name\" --image_file \"{filename}\"")
    else:
        print("\n❌ Failed to capture photo")
        sys.exit(1)

if __name__ == "__main__":
    main()
