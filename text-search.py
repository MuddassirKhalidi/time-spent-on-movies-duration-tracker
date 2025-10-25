#!/usr/bin/env python3
"""
YoloE Custom Object Detection Main Script

This script allows users to specify their own objects to detect in videos,
removing the default 'person' class and enabling custom object detection.
"""

import sys
import argparse
import cv2
import numpy as np
from pathlib import Path
import time
import os
from datetime import datetime

# Add the modules directory to the path to import YoloE
sys.path.append(str(Path(__file__).parent / "modules"))

from YoloE import YoloE, Framedata, AnnotatedFrame


def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="YoloE Custom Object Detection",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py --search "man wearing glasses"
  python main.py --search "car with person inside"
  python main.py --search "dog and cat"
  python main.py --search "person holding bottle"
        """
    )
    
    parser.add_argument(
        "--search", "-s",
        type=str,
        required=True,
        help="Natural language prompt describing objects to detect (e.g., 'man wearing glasses', 'car with person inside')"
    )
    
    return parser.parse_args()


def ensure_targets_folder():
    """Ensure the targets folder exists."""
    targets_dir = Path("targets")
    targets_dir.mkdir(parents=True, exist_ok=True)
    return targets_dir


def save_frame_to_targets(frame, targets_dir):
    """Save the current frame to the targets folder with timestamp."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")[:-3]  # Include milliseconds
    filename = f"target_{timestamp}.jpg"
    filepath = targets_dir / filename
    
    # Convert RGB to BGR for OpenCV saving
    bgr_frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
    
    success = cv2.imwrite(str(filepath), bgr_frame)
    if success:
        print(f"Saved frame to: {filepath}")
    else:
        print(f"Failed to save frame to: {filepath}")


def validate_prompt(prompt_str):
    """Validate the prompt string."""
    if not prompt_str or not prompt_str.strip():
        raise ValueError("Prompt cannot be empty")
    
    prompt = prompt_str.strip()
    
    # Basic validation - ensure prompt has reasonable length
    if len(prompt) < 2:
        raise ValueError("Prompt too short")
    
    if len(prompt) > 200:
        raise ValueError("Prompt too long (max 200 characters)")
    
    return prompt


def setup_yoloe(prompt, confidence, iou):
    """Initialize YoloE with custom prompt."""
    print(f"Initializing YoloE with prompt: '{prompt}'")
    
    # Initialize with default class first to avoid MobileCLIP issues
    yoloe = YoloE(class_names=['person'])
    
    # Update with custom prompt
    print("Updating model with custom prompt...")
    yoloe.update_classes([prompt])
    
    # Set confidence and IoU thresholds
    yoloe._conf = confidence
    yoloe._iou = iou
    
    print(f"YoloE initialized successfully!")
    print(f"Detection prompt: '{prompt}'")
    print(f"Confidence threshold: {confidence}")
    print(f"IoU threshold: {iou}")
    
    return yoloe


def process_video(yoloe, video_source, args):
    """Process video with object detection."""
    print(f"Opening video source: {video_source}")
    
    cap = cv2.VideoCapture(video_source)
    if not cap.isOpened():
        raise ValueError(f"Unable to open video source: {video_source}")
    
    # Get video properties
    fps = int(cap.get(cv2.CAP_PROP_FPS)) or 30
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    
    print(f"Video properties: {width}x{height} @ {fps} FPS")
    
    # Ensure targets folder exists
    targets_dir = ensure_targets_folder()
    print(f"Targets will be saved to: {targets_dir}")
    print("Press 's' to save current frame, 'q' or ESC to quit")
    
    frame_count = 0
    start_time = time.time()
    
    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                print("End of video stream")
                break
            
            # Convert BGR to RGB
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            
            # Create frame data with default settings
            frame_data = Framedata(
                orig_frame=np.array(rgb_frame),
                do_seg=True,      # Enable segmentation by default
                do_det=True,      # Enable detection boxes by default
                do_label=True,    # Enable labels by default
                rm_background=False,  # Keep background by default
                do_blur=False     # No blur by default
            )
            
            # Process frame
            yoloe.put(frame_data)
            
            try:
                annotated_frame = yoloe.get(timeout=1.0)
                
                # Convert back to BGR for display
                result_frame = cv2.cvtColor(annotated_frame.image, cv2.COLOR_RGB2BGR)
                
                # Display frame
                cv2.imshow('YoloE Custom Object Detection', result_frame)
                
                # Check for keyboard input
                key = cv2.waitKey(1) & 0xFF
                if key == ord('q') or key == 27:  # 'q' or ESC
                    print("Quit requested by user")
                    break
                elif key == ord('s'):  # 's' to save frame
                    save_frame_to_targets(annotated_frame.image, targets_dir)
                
                frame_count += 1
                
                # Print progress every 100 frames
                if frame_count % 100 == 0:
                    elapsed = time.time() - start_time
                    fps_current = frame_count / elapsed
                    print(f"Processed {frame_count} frames, FPS: {fps_current:.1f}")
                    
            except Exception as e:
                print(f"Error processing frame {frame_count}: {e}")
                continue
    
    except KeyboardInterrupt:
        print("\nInterrupted by user")
    
    finally:
        # Cleanup
        cap.release()
        cv2.destroyAllWindows()
        yoloe.stop()
        
        # Print final statistics
        total_time = time.time() - start_time
        avg_fps = frame_count / total_time if total_time > 0 else 0
        print(f"\nProcessing complete!")
        print(f"Total frames processed: {frame_count}")
        print(f"Total time: {total_time:.2f} seconds")
        print(f"Average FPS: {avg_fps:.1f}")


def main():
    """Main function."""
    try:
        # Parse arguments
        args = parse_arguments()
        
        # Validate prompt
        prompt = validate_prompt(args.search)
        print(f"Detection prompt: '{prompt}'")
        
        # Use default camera (0) as video source
        video_source = 0
        
        # Setup YoloE with default settings
        yoloe = setup_yoloe(prompt, 0.25, 0.7)
        
        # Process video with default settings
        process_video(yoloe, video_source, args)
        
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
