#!/usr/bin/env python3
"""
Video Recording Script
Records video from camera and saves it to the videos directory.
"""

import cv2
import argparse
import os
import sys
from datetime import datetime
import threading
import time

class VideoRecorder:
    def __init__(self, camera_index=0, output_dir="videos"):
        self.camera_index = camera_index
        self.output_dir = output_dir
        self.cap = None
        self.writer = None
        self.recording = False
        self.frame_width = 1920
        self.frame_height = 1080
        self.fps = 30
        
        # Ensure output directory exists
        os.makedirs(self.output_dir, exist_ok=True)
    
    def initialize_camera(self):
        """Initialize the camera with optimal settings"""
        self.cap = cv2.VideoCapture(self.camera_index)
        
        if not self.cap.isOpened():
            print(f"Error: Could not open camera {self.camera_index}")
            return False
        
        # Set camera properties for better quality
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.frame_width)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.frame_height)
        self.cap.set(cv2.CAP_PROP_FPS, self.fps)
        self.cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*'MJPG'))
        
        # Get actual properties
        actual_width = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        actual_height = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        actual_fps = self.cap.get(cv2.CAP_PROP_FPS)
        
        print(f"Camera initialized:")
        print(f"  Resolution: {actual_width}x{actual_height}")
        print(f"  FPS: {actual_fps}")
        
        return True
    
    def start_recording(self, filename=None):
        """Start recording video"""
        if self.recording:
            print("Already recording!")
            return False
        
        if not self.cap or not self.cap.isOpened():
            print("Camera not initialized!")
            return False
        
        # Generate filename if not provided
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"video_{timestamp}.mp4"
        
        # Ensure filename has .mp4 extension
        if not filename.endswith('.mp4'):
            filename += '.mp4'
        
        # Full path to output file
        output_path = os.path.join(self.output_dir, filename)
        
        # Initialize video writer
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        self.writer = cv2.VideoWriter(
            output_path, 
            fourcc, 
            self.fps, 
            (self.frame_width, self.frame_height)
        )
        
        if not self.writer.isOpened():
            print(f"Error: Could not initialize video writer for {output_path}")
            return False
        
        self.recording = True
        self.output_path = output_path
        print(f"Started recording: {output_path}")
        print("Press 'q' to stop recording, 'ESC' to exit")
        
        return True
    
    def stop_recording(self):
        """Stop recording video"""
        if not self.recording:
            print("Not currently recording!")
            return None
        
        self.recording = False
        
        if self.writer:
            self.writer.release()
            self.writer = None
        
        print(f"Recording stopped. Video saved: {self.output_path}")
        return self.output_path
    
    def record_with_preview(self, filename=None, duration=None):
        """Record video with live preview"""
        if not self.initialize_camera():
            return None
        
        if not self.start_recording(filename):
            return None
        
        start_time = time.time()
        frame_count = 0
        
        try:
            while self.recording:
                ret, frame = self.cap.read()
                if not ret:
                    print("Error: Could not read frame from camera")
                    break
                
                # Write frame to video
                self.writer.write(frame)
                frame_count += 1
                
                # Add recording indicator to frame
                cv2.putText(frame, "REC", (10, 30), 
                           cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
                cv2.putText(frame, f"Frames: {frame_count}", (10, 70), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
                
                # Show preview
                cv2.imshow('Video Recording - Press Q to stop, ESC to exit', frame)
                
                # Check for key presses
                key = cv2.waitKey(1) & 0xFF
                if key == ord('q') or key == ord('Q'):
                    break
                elif key == 27:  # ESC key
                    print("Recording cancelled")
                    break
                
                # Check duration limit
                if duration and (time.time() - start_time) >= duration:
                    print(f"Recording duration limit reached: {duration} seconds")
                    break
        
        except KeyboardInterrupt:
            print("\nRecording interrupted by user")
        
        finally:
            self.stop_recording()
            cv2.destroyAllWindows()
        
        return self.output_path
    
    def record_without_preview(self, filename=None, duration=None):
        """Record video without preview (faster)"""
        if not self.initialize_camera():
            return None
        
        if not self.start_recording(filename):
            return None
        
        start_time = time.time()
        frame_count = 0
        
        print("Recording in progress... (Press Ctrl+C to stop)")
        
        try:
            while self.recording:
                ret, frame = self.cap.read()
                if not ret:
                    print("Error: Could not read frame from camera")
                    break
                
                # Write frame to video
                self.writer.write(frame)
                frame_count += 1
                
                # Print progress every 30 frames
                if frame_count % 30 == 0:
                    elapsed = time.time() - start_time
                    print(f"Recording: {elapsed:.1f}s, {frame_count} frames")
                
                # Check duration limit
                if duration and (time.time() - start_time) >= duration:
                    print(f"Recording duration limit reached: {duration} seconds")
                    break
        
        except KeyboardInterrupt:
            print("\nRecording interrupted by user")
        
        finally:
            self.stop_recording()
        
        return self.output_path
    
    def cleanup(self):
        """Clean up resources"""
        if self.recording:
            self.stop_recording()
        
        if self.cap:
            self.cap.release()
        
        cv2.destroyAllWindows()

def list_available_cameras():
    """List all available cameras"""
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
    parser = argparse.ArgumentParser(description='Record video from camera')
    parser.add_argument('-o', '--output', type=str, help='Output filename (without extension)')
    parser.add_argument('-c', '--camera', type=int, default=0, help='Camera index (default: 0)')
    parser.add_argument('-d', '--duration', type=int, help='Recording duration in seconds')
    parser.add_argument('--no-preview', action='store_true', help='Record without preview (faster)')
    parser.add_argument('--list-cameras', action='store_true', help='List available cameras')
    parser.add_argument('--output-dir', type=str, default='videos', help='Output directory (default: videos)')
    parser.add_argument('--resolution', type=str, choices=['720p', '1080p', '4k'], default='1080p', 
                       help='Recording resolution (default: 1080p)')
    
    args = parser.parse_args()
    
    if args.list_cameras:
        list_available_cameras()
        return
    
    # Set resolution
    resolution_map = {
        '720p': (1280, 720),
        '1080p': (1920, 1080),
        '4k': (3840, 2160)
    }
    
    # Create recorder
    recorder = VideoRecorder(camera_index=args.camera, output_dir=args.output_dir)
    recorder.frame_width, recorder.frame_height = resolution_map[args.resolution]
    
    try:
        if args.no_preview:
            # Record without preview
            output_path = recorder.record_without_preview(args.output, args.duration)
        else:
            # Record with preview
            output_path = recorder.record_with_preview(args.output, args.duration)
        
        if output_path:
            print(f"\n✅ Video recorded successfully!")
            print(f"📁 Saved to: {os.path.abspath(output_path)}")
            
            # Show file size
            file_size = os.path.getsize(output_path)
            file_size_mb = file_size / (1024 * 1024)
            print(f"📊 File size: {file_size_mb:.2f} MB")
        else:
            print("\n❌ Failed to record video")
            sys.exit(1)
    
    except Exception as e:
        print(f"\n❌ Error during recording: {str(e)}")
        sys.exit(1)
    
    finally:
        recorder.cleanup()

if __name__ == "__main__":
    main()
