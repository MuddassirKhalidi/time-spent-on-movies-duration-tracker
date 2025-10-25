import os
import sys
import glob
import cv2
import numpy as np
import queue
import argparse
from datetime import datetime

from PySide6.QtWidgets import (QApplication, QLabel, QMainWindow, QWidget,
                               QVBoxLayout, QLineEdit, QPushButton,
                               QHBoxLayout, QSplitter, QCheckBox, QFrame,
                               QTreeWidget, QTreeWidgetItem, QInputDialog, QDialog,
                               QMessageBox, QFileDialog, QProgressBar, QTextEdit)
from PySide6.QtGui import QImage, QPixmap, QMouseEvent, QKeyEvent, QFont, QPalette, QColor
from PySide6.QtCore import QTimer, Qt, QThread, Signal, QMutex

import time
from pathlib import Path

from modules.capture import CaptureThread, CaptureConfigDialog, VIDEO_CONFIG
from modules.compositor import Compositor, CompositorConfigPopup
from modules.viewer import FrameViewer
from modules.database import FaceDatabase, DatabaseViewerWidget
from modules.tracker import FaceTracker
from modules.MXFace import AnnotatedFrame

class Demo(QMainWindow):
    def __init__(self, video_path='/dev/video0', video_config=None, target_name=None, target_image_file=None, prerecorded_video=None):
        super().__init__()
        self.setWindowTitle("SECURITY MONITORING SYSTEM - Person Detection & Alert")
        
        # Store target parameters
        self.target_name = target_name
        self.target_image_file = target_image_file
        self.prerecorded_video = prerecorded_video
        
        # Apply security theme
        self.apply_security_theme()
        
        # Update window title based on video source
        if self.prerecorded_video:
            self.setWindowTitle(f"SECURITY MONITORING SYSTEM - Processing Video: {self.prerecorded_video}")
        else:
            self.setWindowTitle("SECURITY MONITORING SYSTEM - Person Detection & Alert")
        
        # Create the video display.
        self.viewer = FrameViewer()

        # Set up video capture and processing.
        # Use prerecorded video if specified, otherwise use live camera
        if self.prerecorded_video:
            prerecorded_path = os.path.join("videos", f"{self.prerecorded_video}.mp4")
            if not os.path.exists(prerecorded_path):
                print(f"Error: Prerecorded video file '{prerecorded_path}' not found.")
                print("Available videos in videos/ directory:")
                videos_dir = "videos"
                if os.path.exists(videos_dir):
                    for file in os.listdir(videos_dir):
                        if file.endswith('.mp4'):
                            print(f"  - {file}")
                sys.exit(1)
            print(f"Using prerecorded video: {prerecorded_path}")
            # For prerecorded videos, don't apply video config to preserve original timing
            self.capture_thread = CaptureThread(prerecorded_path, None)
        else:
            self.capture_thread = CaptureThread(video_path, video_config)
        self.face_database = FaceDatabase()
        
        # Load database based on whether specific target is provided
        if self.target_name:
            # Load only the specific target profile
            self.face_database.load_specific_profile('assets/db', self.target_name)
        else:
            # Load all profiles
            self.face_database.load_database_embeddings('assets/db')
        
        self.database_viewer = DatabaseViewerWidget(self.face_database, self.upload_face_image, self.target_name)
        # Pass video FPS to tracker for proper timing
        video_fps = getattr(self.capture_thread, 'video_fps', None)
        self.tracker = FaceTracker(self.face_database, video_fps=video_fps)
        self.compositor = Compositor(self.tracker)
        self.compositor.set_paused(self.capture_thread.pause)

        # Create security-themed buttons
        self.config_popup_button = QPushButton("SYSTEM CONFIG", self)
        self.config_popup_button.clicked.connect(self.open_compositor_config)
        self.config_popup_button.setStyleSheet("""
            QPushButton {
                background-color: #2c3e50;
                color: #ecf0f1;
                border: 2px solid #34495e;
                border-radius: 5px;
                padding: 8px;
                font-weight: bold;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #34495e;
                border-color: #3498db;
            }
            QPushButton:pressed {
                background-color: #1a252f;
            }
        """)

        self.capture_control_button = QPushButton("CAMERA SETUP", self)
        self.capture_control_button.clicked.connect(self.open_capture_config)
        self.capture_control_button.setStyleSheet("""
            QPushButton {
                background-color: #2c3e50;
                color: #ecf0f1;
                border: 2px solid #34495e;
                border-radius: 5px;
                padding: 8px;
                font-weight: bold;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #34495e;
                border-color: #3498db;
            }
            QPushButton:pressed {
                background-color: #1a252f;
            }
        """)

        # Wire signals.
        self.capture_thread.frame_ready.connect(self.tracker.detect)
        self.tracker.frame_ready.connect(self.compositor.draw)
        self.compositor.frame_ready.connect(self.viewer.update_frame)
        self.compositor.frame_ready.connect(self.write_frame_to_video)  # Connect to video recording
        self.viewer.mouse_move.connect(self.compositor.update_mouse_pos)
        self.viewer.mouse_click.connect(self.handle_viewer_mouse_click)

        # Add click-to-pause functionality: clicking anywhere in the viewer toggles capture play/pause
        self.viewer.mouse_click.connect(self.toggle_capture_pause)
        
        # Connect search checking to frame processing
        self.compositor.frame_ready.connect(self.check_for_search_targets)

        self.setup_layout()

        self.tracker.start()
        self.capture_thread.start()
        
        # Update tracker with video FPS after capture thread starts
        if self.prerecorded_video:
            # Wait a moment for capture thread to determine video FPS
            import time
            time.sleep(0.5)  # Give capture thread time to determine FPS
            if hasattr(self.capture_thread, 'video_fps') and self.capture_thread.video_fps is not None:
                print(f"Updating tracker with video FPS: {self.capture_thread.video_fps}")
                self.tracker.video_fps = self.capture_thread.video_fps
        
        self.timestamps = [0] * 30

        self.fps_timer = QTimer(self)
        self.fps_timer.setInterval(500)
        self.fps_timer.timeout.connect(self.poll_framerates)
        self.fps_timer.start()

        # Create a persistent instance for the config popup.
        self.config_popup = None
        
        # Search functionality
        self.search_targets = set()  # Set of person names to search for
        self.last_found_persons = set()  # Track which persons were found in the last frame
        
        # Security alert system
        self.alert_active = False
        self.alert_timer = QTimer(self)
        self.alert_timer.timeout.connect(self.clear_alert)
        self.alert_timer.setSingleShot(True)
        
        # Video recording functionality
        self.video_recording = False
        self.video_writer = None
        self.matched_videos_dir = "matched_videos"
        self.ensure_matched_videos_directory()
        
        # Initialize search targets from existing database
        self.update_search_targets()
        
        # Process target image if provided
        if self.target_name and self.target_image_file:
            self.process_target_image_on_startup()

    def apply_security_theme(self):
        """Apply security-themed styling to the application"""
        # Set dark theme palette
        palette = QPalette()
        palette.setColor(QPalette.Window, QColor(30, 30, 30))  # Dark background
        palette.setColor(QPalette.WindowText, QColor(220, 220, 220))  # Light text
        palette.setColor(QPalette.Base, QColor(40, 40, 40))  # Darker base
        palette.setColor(QPalette.AlternateBase, QColor(50, 50, 50))
        palette.setColor(QPalette.ToolTipBase, QColor(0, 0, 0))
        palette.setColor(QPalette.ToolTipText, QColor(220, 220, 220))
        palette.setColor(QPalette.Text, QColor(220, 220, 220))
        palette.setColor(QPalette.Button, QColor(50, 50, 50))
        palette.setColor(QPalette.ButtonText, QColor(220, 220, 220))
        palette.setColor(QPalette.BrightText, QColor(255, 0, 0))  # Red for alerts
        palette.setColor(QPalette.Link, QColor(42, 130, 218))
        palette.setColor(QPalette.Highlight, QColor(42, 130, 218))
        palette.setColor(QPalette.HighlightedText, QColor(255, 255, 255))
        
        self.setPalette(palette)
        
        # Set application-wide stylesheet
        self.setStyleSheet("""
            QMainWindow {
                background-color: #1e1e1e;
                color: #dcdcdc;
            }
            QWidget {
                background-color: #1e1e1e;
                color: #dcdcdc;
            }
            QSplitter::handle {
                background-color: #404040;
            }
            QSplitter::handle:horizontal {
                width: 3px;
            }
            QSplitter::handle:vertical {
                height: 3px;
            }
        """)

    def setup_layout(self):
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.central_widget.setMinimumSize(300, 200)
        self.main_layout = QHBoxLayout(self.central_widget)

        # Splitter to separate control panel and video viewer.
        self.splitter = QSplitter(Qt.Horizontal)
        self.main_layout.addWidget(self.splitter)

        # Left control panel.
        self.control_panel = QWidget()
        self.control_panel.setFixedWidth(320)
        self.control_panel.setStyleSheet("""
            QWidget {
                background-color: #2c2c2c;
                border-right: 2px solid #404040;
            }
        """)
        self.control_layout = QVBoxLayout(self.control_panel)
        self.splitter.addWidget(self.control_panel)

        # Security system header
        header_frame = QFrame()
        header_frame.setStyleSheet("""
            QFrame {
                background-color: #1a1a1a;
                border: 2px solid #e74c3c;
                border-radius: 8px;
                margin: 5px;
            }
        """)
        header_layout = QVBoxLayout(header_frame)
        
        # System title
        title_label = QLabel("SECURITY MONITORING")
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setStyleSheet("""
            QLabel {
                color: #e74c3c;
                font-size: 16px;
                font-weight: bold;
                padding: 5px;
            }
        """)
        header_layout.addWidget(title_label)
        
        # Status indicator
        if self.prerecorded_video:
            status_text = f"PROCESSING VIDEO: {self.prerecorded_video}"
        else:
            status_text = "SYSTEM ACTIVE"
        
        self.status_label = QLabel(status_text)
        self.status_label.setAlignment(Qt.AlignCenter)
        self.status_label.setStyleSheet("""
            QLabel {
                color: #27ae60;
                font-size: 12px;
                font-weight: bold;
                padding: 3px;
            }
        """)
        header_layout.addWidget(self.status_label)
        
        self.control_layout.addWidget(header_frame)

        # Alert display
        self.alert_frame = QFrame()
        self.alert_frame.setStyleSheet("""
            QFrame {
                background-color: #2c2c2c;
                border: 1px solid #404040;
                border-radius: 5px;
                margin: 5px;
            }
        """)
        alert_layout = QVBoxLayout(self.alert_frame)
        
        alert_title = QLabel("ALERT STATUS")
        alert_title.setAlignment(Qt.AlignCenter)
        alert_title.setStyleSheet("""
            QLabel {
                color: #f39c12;
                font-size: 12px;
                font-weight: bold;
            }
        """)
        alert_layout.addWidget(alert_title)
        
        self.alert_label = QLabel("NO ALERTS")
        self.alert_label.setAlignment(Qt.AlignCenter)
        self.alert_label.setStyleSheet("""
            QLabel {
                color: #27ae60;
                font-size: 14px;
                font-weight: bold;
                padding: 5px;
            }
        """)
        alert_layout.addWidget(self.alert_label)
        
        self.control_layout.addWidget(self.alert_frame)

        # Add logo at the top of control panel
        logo_label = QLabel()
        logo_pixmap = QPixmap("assets/mx-logo.png")
        logo_label.setPixmap(logo_pixmap.scaledToWidth(200, Qt.SmoothTransformation))
        logo_label.setAlignment(Qt.AlignCenter)
        logo_label.setStyleSheet("QLabel { background-color: transparent; }")
        self.control_layout.addWidget(logo_label)

        # Control buttons section
        controls_frame = QFrame()
        controls_frame.setStyleSheet("""
            QFrame {
                background-color: #2c2c2c;
                border: 1px solid #404040;
                border-radius: 5px;
                margin: 5px;
            }
        """)
        controls_layout = QVBoxLayout(controls_frame)
        
        controls_title = QLabel("SYSTEM CONTROLS")
        controls_title.setAlignment(Qt.AlignCenter)
        controls_title.setStyleSheet("""
            QLabel {
                color: #3498db;
                font-size: 12px;
                font-weight: bold;
                padding: 5px;
            }
        """)
        controls_layout.addWidget(controls_title)
        
        # Add the capture config and compositor config buttons.
        controls_layout.addWidget(self.capture_control_button)
        controls_layout.addWidget(self.config_popup_button)
        
        # Add upload button for face images
        self.upload_button = QPushButton("ADD TARGET IMAGES", self)
        self.upload_button.clicked.connect(self.upload_face_image)
        self.upload_button.setStyleSheet("""
            QPushButton {
                background-color: #2c3e50;
                color: #ecf0f1;
                border: 2px solid #34495e;
                border-radius: 5px;
                padding: 8px;
                font-weight: bold;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #34495e;
                border-color: #3498db;
            }
            QPushButton:pressed {
                background-color: #1a252f;
            }
        """)
        controls_layout.addWidget(self.upload_button)
        
        # Add video recording button
        self.record_button = QPushButton("START RECORDING", self)
        self.record_button.clicked.connect(self.toggle_video_recording)
        self.record_button.setStyleSheet("""
            QPushButton {
                background-color: #e74c3c;
                color: #ecf0f1;
                border: 2px solid #c0392b;
                border-radius: 5px;
                padding: 8px;
                font-weight: bold;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #c0392b;
                border-color: #3498db;
            }
            QPushButton:pressed {
                background-color: #a93226;
            }
        """)
        controls_layout.addWidget(self.record_button)
        
        self.control_layout.addWidget(controls_frame)
        
        # Database viewer with security styling
        db_frame = QFrame()
        db_frame.setStyleSheet("""
            QFrame {
                background-color: #2c2c2c;
                border: 1px solid #404040;
                border-radius: 5px;
                margin: 5px;
            }
        """)
        db_layout = QVBoxLayout(db_frame)
        
        db_title = QLabel("TARGET DATABASE")
        db_title.setAlignment(Qt.AlignCenter)
        db_title.setStyleSheet("""
            QLabel {
                color: #9b59b6;
                font-size: 12px;
                font-weight: bold;
                padding: 5px;
            }
        """)
        db_layout.addWidget(db_title)
        
        db_layout.addWidget(self.database_viewer)
        self.control_layout.addWidget(db_frame)

        # Right: Video viewer.
        self.splitter.addWidget(self.viewer)
        self.splitter.setStretchFactor(1, 1)

    def open_compositor_config(self):
        if self.config_popup is None:
            self.config_popup = CompositorConfigPopup(self.compositor, self)
        self.config_popup.show()
        self.config_popup.raise_()

    def open_capture_config(self):
        current_resolution = "2k"
        for res in ["1080p", "2k", "4k"]:
            if VIDEO_CONFIG.get(res) == self.capture_thread.video_config:
                current_resolution = res
                break

        dialog = CaptureConfigDialog(self.capture_thread.video_source, current_resolution, self)
        if dialog.exec() == QDialog.Accepted:
            new_video_path, new_resolution = dialog.get_configuration()
            print(f"Applying new capture configuration: {new_video_path}, {new_resolution}")
            self.capture_thread.stop()
            self.capture_thread.wait()
            new_config = VIDEO_CONFIG.get(new_resolution, self.capture_thread.video_config)
            self.capture_thread = CaptureThread(new_video_path, new_config)
            self.capture_thread.frame_ready.connect(self.tracker.detect)
            self.capture_thread.start()

    def handle_viewer_mouse_click(self, mouse_pos):
        # Face-capture functionality has been removed
        # Only click-to-pause functionality remains
        pass

    def toggle_capture_pause(self, pos):
        """Toggle play/pause of the capture thread when the viewer is clicked."""
        if pos is None:
            return

        # Toggle pause/play on any click
        self.capture_thread.toggle_play()
        state = "paused" if self.capture_thread.pause else "running"
        print(f"Capture thread {state}")
        self.compositor.set_paused(self.capture_thread.pause)
        
        # Update status display
        self.update_status_display()

    def update_status_display(self):
        """Update the status display based on system state"""
        if self.capture_thread.pause:
            self.status_label.setText("SYSTEM PAUSED")
            self.status_label.setStyleSheet("""
                QLabel {
                    color: #f39c12;
                    font-size: 12px;
                    font-weight: bold;
                    padding: 3px;
                }
            """)
        else:
            self.status_label.setText("SYSTEM ACTIVE")
            self.status_label.setStyleSheet("""
                QLabel {
                    color: #27ae60;
                    font-size: 12px;
                    font-weight: bold;
                    padding: 3px;
                }
            """)

    def check_for_search_targets(self):
        """Check if any search targets are currently visible and alert if found"""
        if not self.search_targets:
            return
            
        tracked_objects = self.tracker.get_activated_tracker_objects()
        current_found_persons = set()
        
        for obj in tracked_objects:
            if obj.name and obj.name in self.search_targets:
                current_found_persons.add(obj.track_id)
                
                # Alert if this person wasn't found in the previous frame
                if obj.track_id not in self.last_found_persons:
                    self.trigger_security_alert(obj.name)
        
        # Update tracking
        self.last_found_persons = current_found_persons

    def trigger_security_alert(self, person_name):
        """Trigger a security alert when a target person is detected"""
        print(f"SECURITY ALERT: Target '{person_name}' detected!")
        
        # Update alert display
        self.alert_label.setText(f"TARGET DETECTED:\n{person_name}")
        self.alert_label.setStyleSheet("""
            QLabel {
                color: #e74c3c;
                font-size: 14px;
                font-weight: bold;
                padding: 5px;
                background-color: #2c2c2c;
                border: 2px solid #e74c3c;
                border-radius: 5px;
            }
        """)
        
        # Update alert frame styling
        self.alert_frame.setStyleSheet("""
            QFrame {
                background-color: #2c2c2c;
                border: 2px solid #e74c3c;
                border-radius: 5px;
                margin: 5px;
            }
        """)
        
        # Set alert as active
        self.alert_active = True
        
        # Clear alert after 5 seconds
        self.alert_timer.start(5000)

    def clear_alert(self):
        """Clear the security alert display"""
        self.alert_active = False
        
        # Reset alert display
        self.alert_label.setText("NO ALERTS")
        self.alert_label.setStyleSheet("""
            QLabel {
                color: #27ae60;
                font-size: 14px;
                font-weight: bold;
                padding: 5px;
            }
        """)
        
        # Reset alert frame styling
        self.alert_frame.setStyleSheet("""
            QFrame {
                background-color: #2c2c2c;
                border: 1px solid #404040;
                border-radius: 5px;
                margin: 5px;
            }
        """)

    def update_search_targets(self):
        """Update search targets based on current database profiles"""
        # If a specific target name is provided, only search for that target
        if self.target_name:
            self.search_targets = {self.target_name}
            print(f"Search targets updated (specific target): {self.search_targets}")
        else:
            # Get all profile names from the database
            self.search_targets = set()
            for profile_name in self.face_database.database.keys():
                if profile_name != 'Unknown':  # Don't search for unknown faces
                    self.search_targets.add(profile_name)
            print(f"Search targets updated (all targets): {self.search_targets}")
        
        # Update compositor with search targets
        self.compositor.set_search_targets(self.search_targets)

    def ensure_matched_videos_directory(self):
        """Ensure the matched_videos directory exists"""
        os.makedirs(self.matched_videos_dir, exist_ok=True)
        print(f"Matched videos will be saved to: {self.matched_videos_dir}")

    def start_video_recording(self):
        """Start recording the processed video"""
        if self.video_recording:
            print("Already recording video!")
            return False
        
        # Generate filename with timestamp and target name
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        target_suffix = f"_{self.target_name}" if self.target_name else ""
        filename = f"matched_video{target_suffix}_{timestamp}.mp4"
        output_path = os.path.join(self.matched_videos_dir, filename)
        
        # Get video properties from capture thread
        if hasattr(self.capture_thread, 'video_fps') and self.capture_thread.video_fps:
            fps = self.capture_thread.video_fps
        else:
            fps = 30  # Default FPS
        
        # Get frame dimensions from the viewer
        frame_width = 1920  # Default width
        frame_height = 1080  # Default height
        
        # Initialize video writer
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        self.video_writer = cv2.VideoWriter(output_path, fourcc, fps, (frame_width, frame_height))
        
        if not self.video_writer.isOpened():
            print(f"Error: Could not initialize video writer for {output_path}")
            return False
        
        self.video_recording = True
        self.video_output_path = output_path
        print(f"Started recording matched video: {output_path}")
        return True

    def stop_video_recording(self):
        """Stop recording the processed video"""
        if not self.video_recording:
            print("Not currently recording video!")
            return None
        
        self.video_recording = False
        
        if self.video_writer:
            self.video_writer.release()
            self.video_writer = None
        
        print(f"Stopped recording. Video saved: {self.video_output_path}")
        return self.video_output_path

    def write_frame_to_video(self, frame):
        """Write a frame to the video if recording is active"""
        if self.video_recording and self.video_writer:
            # Convert RGB to BGR for OpenCV video writer
            if len(frame.shape) == 3 and frame.shape[2] == 3:
                bgr_frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
            else:
                bgr_frame = frame
            
            self.video_writer.write(bgr_frame)

    def toggle_video_recording(self):
        """Toggle video recording on/off"""
        if not self.video_recording:
            if self.start_video_recording():
                self.record_button.setText("STOP RECORDING")
                self.record_button.setStyleSheet("""
                    QPushButton {
                        background-color: #27ae60;
                        color: #ecf0f1;
                        border: 2px solid #229954;
                        border-radius: 5px;
                        padding: 8px;
                        font-weight: bold;
                        font-size: 12px;
                    }
                    QPushButton:hover {
                        background-color: #229954;
                        border-color: #3498db;
                    }
                    QPushButton:pressed {
                        background-color: #1e8449;
                    }
                """)
        else:
            output_path = self.stop_video_recording()
            self.record_button.setText("START RECORDING")
            self.record_button.setStyleSheet("""
                QPushButton {
                    background-color: #e74c3c;
                    color: #ecf0f1;
                    border: 2px solid #c0392b;
                    border-radius: 5px;
                    padding: 8px;
                    font-weight: bold;
                    font-size: 12px;
                }
                QPushButton:hover {
                    background-color: #c0392b;
                    border-color: #3498db;
                }
                QPushButton:pressed {
                    background-color: #a93226;
                }
            """)
            if output_path:
                print(f"✅ Video saved successfully: {output_path}")

    def upload_face_image(self):
        """Handle uploading a face image from disk"""
        # Open file dialog to select image
        file_path, _ = QFileDialog.getOpenFileName(
            self, 
            "Add More Images to Search Query", 
            "", 
            "Image Files (*.png *.jpg *.jpeg *.bmp *.tiff)"
        )
        
        if file_path:
            self.process_uploaded_image(file_path)
    
    def process_uploaded_image(self, image_path):
        """Process uploaded image: detect faces, generate embeddings, and save to database"""
        try:
            # Load the image
            image = cv2.imread(image_path)
            if image is None:
                QMessageBox.warning(self, "Error", "Could not load the selected image.")
                return
            
            # Convert BGR to RGB for processing
            image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            
            print(f"Processing uploaded image: {image_path}")
            print(f"Image shape: {image_rgb.shape}")
            
            # Detect faces in the uploaded image
            detected_faces = self.detect_faces_in_image(image_rgb)
            
            if not detected_faces:
                QMessageBox.information(self, "No Faces Found", "No faces were detected in the uploaded image.")
                return
            
            print(f"Detected {len(detected_faces)} face(s)")
            
            # If multiple faces detected, let user choose which one
            if len(detected_faces) > 1:
                face_index = self.select_face_from_multiple(detected_faces, image_rgb)
                if face_index is None:
                    return  # User cancelled
                detected_faces = [detected_faces[face_index]]
            
            # Process the selected face using the same logic as mouse click
            face = detected_faces[0]
            self.process_face_like_mouse_click(face, image_rgb)
            
            QMessageBox.information(self, "Success", "Face image uploaded and processed successfully!")
            
            # Update search targets after adding new face
            self.update_search_targets()
            
        except Exception as e:
            print(f"Error processing image: {str(e)}")
            QMessageBox.critical(self, "Error", f"An error occurred while processing the image: {str(e)}")
    
    def detect_faces_in_image(self, image):
        """Detect faces in a static image by temporarily pausing DetectionThread"""
        print("Starting face detection...")
        
        # Temporarily pause the DetectionThread to prevent it from consuming our results
        self.tracker.detection_thread.stop_threads = True
        
        try:
            # Wait a moment for the thread to stop processing
            time.sleep(0.1)
            
            # Put the image through detection
            self.tracker.mxface.detect_put(image, block=True, timeout=5.0)
            
            # Get detection results
            try:
                result_frame = self.tracker.mxface.detect_get(block=True, timeout=5.0)
                print(f"Detection completed. Found {len(result_frame.boxes)} potential faces")
            except queue.Empty:
                print("Detection timeout - no faces found")
                return []
            
            detected_faces = []
            for i, (bbox, keypoints, score) in enumerate(zip(result_frame.boxes, result_frame.keypoints, result_frame.scores)):
                print(f"Face {i}: score={score:.3f}, bbox={bbox}")
                if score > 0.7:  # Confidence threshold
                    detected_faces.append({
                        'bbox': bbox,
                        'keypoints': keypoints,
                        'score': score
                    })
                    print(f"Face {i} detected successfully")
            
            print(f"Total detected faces: {len(detected_faces)}")
            return detected_faces
            
        finally:
            # Restart the DetectionThread
            self.tracker.detection_thread.stop_threads = False
            if not self.tracker.detection_thread.isRunning():
                self.tracker.detection_thread.start()
    
    def process_face_like_mouse_click(self, face_data, image):
        """Process uploaded face exactly like a mouse click"""
        bbox = face_data['bbox']
        keypoints = face_data['keypoints']
        
        # Extract face region exactly like in handle_viewer_mouse_click
        x, y, w, h = bbox
        margin = 10
        bbox_size = max(w, h) + 2 * margin
        center_x, center_y = x + w // 2, y + h // 2
        x_start = max(0, center_x - bbox_size // 2)
        x_end = min(image.shape[1], center_x + bbox_size // 2)
        y_start = max(0, center_y - bbox_size // 2)
        y_end = min(image.shape[0], center_y + bbox_size // 2)
        cropped_frame = image[y_start:y_end, x_start:x_end]
        
        # Create a fake tracked object to get embedding
        fake_obj = type('obj', (), {
            'bbox': (x_start, y_start, x_end, y_end),
            'keypoints': keypoints,
            'name': 'Unknown',
            'embedding': np.zeros([128])  # Will be filled by recognition
        })()
        
        # Use a special track_id for manual uploads and add to tracker_dict temporarily
        track_id = 999  # Special ID for manual uploads
        
        # Add the fake object to tracker_dict so RecognitionThread will process it
        with self.tracker.tracker_dict_lock:
            self.tracker.tracker_dict[track_id] = fake_obj
        
        try:
            # Put through recognition queue
            self.tracker.mxface.recognize_put(
                (track_id, image, (x, y, x + w, y + h), (keypoints[0], keypoints[1])), 
                block=True, timeout=10.0
            )
            
            # Wait for recognition result with longer timeout
            start_time = time.time()
            embedding = None
            while time.time() - start_time < 10.0:
                with self.tracker.tracker_dict_lock:
                    if track_id in self.tracker.tracker_dict:
                        obj = self.tracker.tracker_dict[track_id]
                        if obj.embedding is not None and np.linalg.norm(obj.embedding) > 0:
                            embedding = obj.embedding
                            break
                time.sleep(0.1)
            
            if embedding is None:
                print("Recognition timeout - no embedding generated")
                return
                
            fake_obj.embedding = embedding
            print(f"Generated embedding with norm: {np.linalg.norm(embedding):.3f}")
            
        except Exception as e:
            print(f"Recognition error: {str(e)}")
            return
        finally:
            # Clean up the temporary tracker entry
            with self.tracker.tracker_dict_lock:
                if track_id in self.tracker.tracker_dict:
                    del self.tracker.tracker_dict[track_id]
        
        # Save to database exactly like mouse click
        profile_path = self.database_viewer.get_selected_directory()
        if not profile_path:
            # Use target name if provided via command line, otherwise prompt user
            if self.target_name:
                new_profile = self.target_name
                profile_path = os.path.join(self.database_viewer.db_path, new_profile)
                if not os.path.exists(profile_path):
                    os.makedirs(profile_path)
            else:
                new_profile = self.database_viewer.add_profile()
                if not new_profile:
                    return
                profile_path = os.path.join(self.database_viewer.db_path, new_profile)
        
        if os.path.exists(profile_path) and Path(profile_path) != Path(self.database_viewer.db_path):
            i = 0
            while os.path.exists(os.path.join(profile_path, f"{i}.jpg")):
                i += 1
            filename = os.path.join(profile_path, f"{i}.jpg")
            
            print(f'Saving image to {filename}')
            cv2.imwrite(filename, cv2.cvtColor(cropped_frame, cv2.COLOR_RGB2BGR))
            self.database_viewer.load_profiles()
            self.face_database.add_to_database(fake_obj.embedding, filename)
    
    def select_face_from_multiple(self, detected_faces, image):
        """Let user select which face to use when multiple faces are detected"""
        # For now, just return the first face (highest confidence)
        # In a more sophisticated implementation, you could show a dialog with face thumbnails
        return 0
    
    def process_target_image_on_startup(self):
        """Process the target image provided via command line arguments"""
        try:
            # Construct full path to the target image
            target_image_path = os.path.join("targets", self.target_image_file)
            
            if not os.path.exists(target_image_path):
                print(f"Error: Target image file '{target_image_path}' not found.")
                return
            
            print(f"Processing target image: {target_image_path} for person: {self.target_name}")
            
            # Load the image
            image = cv2.imread(target_image_path)
            if image is None:
                print(f"Error: Could not load the target image: {target_image_path}")
                return
            
            # Convert BGR to RGB for processing
            image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            
            print(f"Image shape: {image_rgb.shape}")
            
            # Detect faces in the target image
            detected_faces = self.detect_faces_in_image(image_rgb)
            
            if not detected_faces:
                print("Error: No faces were detected in the target image.")
                return
            
            print(f"Detected {len(detected_faces)} face(s)")
            
            # If multiple faces detected, use the first one (highest confidence)
            if len(detected_faces) > 1:
                print("Multiple faces detected, using the first one (highest confidence)")
            
            # Process the selected face
            face = detected_faces[0]
            self.process_target_face_automatically(face, image_rgb, target_image_path)
            
            print(f"Successfully processed target image for '{self.target_name}'")
            
        except Exception as e:
            print(f"Error processing target image: {str(e)}")
            import traceback
            traceback.print_exc()
    
    def process_target_face_automatically(self, face_data, image, target_image_path):
        """Process target face automatically without UI interaction"""
        bbox = face_data['bbox']
        keypoints = face_data['keypoints']
        
        # Extract face region exactly like in handle_viewer_mouse_click
        x, y, w, h = bbox
        margin = 10
        bbox_size = max(w, h) + 2 * margin
        center_x, center_y = x + w // 2, y + h // 2
        x_start = max(0, center_x - bbox_size // 2)
        x_end = min(image.shape[1], center_x + bbox_size // 2)
        y_start = max(0, center_y - bbox_size // 2)
        y_end = min(image.shape[0], center_y + bbox_size // 2)
        cropped_frame = image[y_start:y_end, x_start:x_end]
        
        # Create a fake tracked object to get embedding
        fake_obj = type('obj', (), {
            'bbox': (x_start, y_start, x_end, y_end),
            'keypoints': keypoints,
            'name': 'Unknown',
            'embedding': np.zeros([128])  # Will be filled by recognition
        })()
        
        # Use a special track_id for manual uploads and add to tracker_dict temporarily
        track_id = 999  # Special ID for manual uploads
        
        # Add the fake object to tracker_dict so RecognitionThread will process it
        with self.tracker.tracker_dict_lock:
            self.tracker.tracker_dict[track_id] = fake_obj
        
        try:
            # Put through recognition queue
            self.tracker.mxface.recognize_put(
                (track_id, image, (x, y, x + w, y + h), (keypoints[0], keypoints[1])), 
                block=True, timeout=10.0
            )
            
            # Wait for recognition result with longer timeout
            start_time = time.time()
            embedding = None
            while time.time() - start_time < 10.0:
                with self.tracker.tracker_dict_lock:
                    if track_id in self.tracker.tracker_dict:
                        obj = self.tracker.tracker_dict[track_id]
                        if obj.embedding is not None and np.linalg.norm(obj.embedding) > 0:
                            embedding = obj.embedding
                            break
                time.sleep(0.1)
            
            if embedding is None:
                print("Recognition timeout - no embedding generated")
                return
                
            fake_obj.embedding = embedding
            print(f"Generated embedding with norm: {np.linalg.norm(embedding):.3f}")
            
        except Exception as e:
            print(f"Recognition error: {str(e)}")
            return
        finally:
            # Clean up the temporary tracker entry
            with self.tracker.tracker_dict_lock:
                if track_id in self.tracker.tracker_dict:
                    del self.tracker.tracker_dict[track_id]
        
        # Create profile directory automatically
        profile_path = os.path.join(self.database_viewer.db_path, self.target_name)
        if not os.path.exists(profile_path):
            os.makedirs(profile_path)
            print(f"Created profile directory: {profile_path}")
        
        # Save the cropped face image
        if os.path.exists(profile_path):
            i = 0
            while os.path.exists(os.path.join(profile_path, f"{i}.jpg")):
                i += 1
            filename = os.path.join(profile_path, f"{i}.jpg")
            
            print(f'Saving image to {filename}')
            cv2.imwrite(filename, cv2.cvtColor(cropped_frame, cv2.COLOR_RGB2BGR))
            
            # Add to database
            self.face_database.add_to_database(fake_obj.embedding, filename)
            print(f"Added {self.target_name} to face database")
            
            # Reload the database viewer to show the new profile
            self.database_viewer.load_profiles()
            
            # Update search targets to include the new person
            self.update_search_targets()

    def poll_framerates(self):
        # If paused, redraw the last known frame so the overlay shows.
        if self.capture_thread.pause:
            if hasattr(self.tracker, "current_frame") and self.tracker.current_frame is not None:
                frame = np.copy(self.tracker.current_frame.image)
                self.compositor.draw(frame)

    def closeEvent(self, event):
        # Stop video recording if active
        if self.video_recording:
            self.stop_video_recording()
        
        self.capture_thread.stop()
        self.capture_thread.wait()
        self.tracker.stop()
        self.fps_timer.stop()
        super().closeEvent(event)

if __name__ == "__main__":
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Security Monitoring System - Person Detection & Alert')
    parser.add_argument('--name', type=str, help='Label of the person to be detected')
    parser.add_argument('--image_file', type=str, help='Sample image file of the person to be detected (should be in targets/ directory)')
    parser.add_argument('--prerecorded', type=str, help='Process prerecorded video (filename without extension, located in src/videos/ directory)')
    
    args = parser.parse_args()
    
    app = QApplication(sys.argv)
    
    # Determine video source
    if args.prerecorded:
        # Use prerecorded video
        video_path = None  # Will be set in Demo.__init__
        print(f"Processing prerecorded video: {args.prerecorded}")
    else:
        # Use live camera
        video_path = "/dev/video0"  # Update this path as needed.
        streams = sorted(glob.glob('/dev/video*'))

        if not streams:
            video_path = 'assets/mx-logo.png'
        else:
            video_path = streams[0] 

    player = Demo(video_path, VIDEO_CONFIG['2k'], args.name, args.image_file, args.prerecorded)
    player.resize(1400, 900)  # Slightly larger for better security interface
    player.show()
    sys.exit(app.exec())