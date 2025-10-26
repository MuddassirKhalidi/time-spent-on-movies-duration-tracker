# Multimodal Search Application

A comprehensive security monitoring and object detection system supporting both text-based natural language object search and face recognition with real-time tracking and alerting.

## Features

- **Text-Based Object Detection**: Use natural language prompts to detect custom objects in real-time video streams using YoloE
- **Face Recognition & Tracking**: Real-time face detection, recognition, and tracking using deep learning models
- **Security Alert System**: Automated alerts when target persons are detected
- **GUI Interface**: PySide6-based graphical interface for monitoring and configuration
- **Video Recording**: Record video clips when target persons are detected
- **Pre-recorded Video Processing**: Process offline video files for analysis
- **Photo & Video Capture**: Utilities to capture photos and record videos from camera

## System Components

### Main Applications

1. **text-search.py** - Text-based object detection with YoloE
2. **img-search.py** - GUI-based face recognition and security monitoring
3. **capture_photo.py** - Photo capture utility
4. **record_video.py** - Video recording utility

### Core Modules

- `modules/YoloE.py` - YoloE object detection implementation
- `modules/MXFace.py` - Face detection and recognition using Memryx MXFace
- `modules/tracker.py` - BYTETracker for object tracking
- `modules/database.py` - Face database management
- `modules/capture.py` - Video capture thread handling
- `modules/compositor.py` - Frame composition and visualization
- `modules/viewer.py` - GUI frame viewer
- `modules/bytetracker/` - BYTE tracking implementation

## Installation

### Prerequisites

- Python 3.8 or higher
- OpenCV (cv2)
- PyTorch
- PySide6
- NumPy
- Pillow
- Matplotlib
- Ultralytics YOLO
- Memryx Neural Compiler

### Step 1: Install Python Dependencies

```bash
pip install -r requirements.txt
```

### Step 2: Download Models

#### For Text Search (YoloE):

Download and prepare the precompiled DFPs:

```bash
wget https://developer.memryx.com/example_files/YoloE-v8s-seg_640_640_3_onnx.zip
mkdir -p models
unzip YoloE-v8s-seg_640_640_3_onnx.zip -d models
```

This creates:
- `models/yoloe-v8s-seg_post.onnx` - Post-processing model
- `models/yoloe-v8s-seg.dfp` - Pre-compiled DFP file

#### For Image Search (YoloV8n-Face, FaceNet):

Download and prepare the face recognition models:

```bash
wget https://developer.memryx.com/example_files/2p0/face_recognition.zip
mkdir -p models-img-search
unzip face_recognition.zip -d models-img-search
```

## Usage

### Text-Based Object Detection

Search for objects using natural language prompts:

```bash
python text-search.py --search "man wearing glasses"
```

**Examples:**
```bash
# Detect people wearing glasses
python text-search.py --search "person wearing glasses"

# Detect cars with people inside
python text-search.py --search "car with person inside"

# Detect multiple objects
python text-search.py --search "dog and cat together"

# Detect people holding objects
python text-search.py --search "person holding bottle"
```

**Controls:**
- Press `'s'` to save current frame to `targets/` folder
- Press `'q'` or `ESC` to quit

**Output:**
- Saved frames are stored in `targets/target_YYYYMMDD_HHMMSS_mmm.jpg`

### Face Recognition & Security Monitoring

Run the GUI security monitoring system:

```bash
python img-search.py
```

#### Processing a Specific Target Person

```bash
python img-search.py --name "John Doe" --image_file "photo_20240101_120000.jpg"
```

**Add Target Photos First:**
```bash
# Capture a photo to use as target
python capture_photo.py -o targets/photo_name.jpg

# Then run the search
python img-search.py --name "John Doe" --image_file "photo_name.jpg"
```

#### Processing Pre-recorded Videos

```bash
# Record a video first
python record_video.py -output my_video

# Process the recorded video
python img-search.py --prerecorded my_video
```

**GUI Features:**
- **SYSTEM CONFIG** - Configure compositor settings
- **CAMERA SETUP** - Change camera source and resolution
- **ADD TARGET IMAGES** - Upload additional face images to database
- **START RECORDING** - Record video when target is detected

**Controls:**
- Click anywhere in video viewer to pause/resume
- Automatic alerts when target persons are detected
- Recorded videos saved to `matched_videos/` directory

### Photo Capture Utility

Capture photos from camera:

```bash
# Interactive capture with preview
python capture_photo.py

# Save to specific location
python capture_photo.py -output targets/my_photo.jpg

# Capture immediately without preview
python capture_photo.py --no-preview

# Specify camera index
python capture_photo.py -c 1

# List available cameras
python capture_photo.py --list-cameras
```

### Video Recording Utility

Record videos from camera:

```bash
# Interactive recording with preview
python record_video.py

# Save to specific filename
python record_video.py -output my_video

# Record specific duration
python record_video.py -d 60

# Record without preview (faster)
python record_video.py --no-preview

# Specify resolution
python record_video.py --resolution 4k

# Specify output directory
python record_video.py --output-dir custom_videos
```

## Directory Structure

```
src_multimodal-search/
├── assets/
│   ├── db/              # Face database (auto-created)
│   └── mx-logo.png
├── modules/
│   ├── bytetracker/     # ByteTrack implementation
│   ├── capture.py        # Video capture handling
│   ├── compositor.py    # Frame composition
│   ├── database.py      # Face database management
│   ├── MXFace.py        # Face detection/recognition
│   ├── ObjectGrouper.py
│   ├── spatial_analyzer.py
│   ├── tracker.py       # Face tracker
│   ├── utils.py
│   ├── viewer.py        # GUI viewer
│   └── YoloE.py         # YoloE implementation
├── models/              # YoloE models (downloaded)
├── models-img-search/   # MXFace models
├── targets/             # Captured photos (auto-created)
├── videos/              # Recorded videos (auto-created)
├── matched_videos/      # Videos with detected targets (auto-created)
├── text-search.py       # Text-based object detection
├── img-search.py        # Face recognition GUI
├── capture_photo.py    # Photo capture utility
├── record_video.py     # Video recording utility
├── requirements.txt
└── README.md
```

## Workflows

### Workflow 1: Text-Based Object Detection

1. Start the text search application:
   ```bash
   python text-search.py --search "person wearing red shirt"
   ```

2. Camera feed opens with object detection overlay

3. Press `'s'` to save frames when objects are detected

4. Saved frames go to `targets/` directory

### Workflow 2: Face Recognition & Monitoring

1. **Setup Phase:**
   ```bash
   # Capture target photos
   python capture_photo.py -o targets/person1.jpg
   python capture_photo.py -o targets/person2.jpg
   
   # Start monitoring with specific target
   python img-search.py --name "Person1" --image_file "person1.jpg"
   ```

2. **Face Database Setup:**
   - Start the GUI: `python img-search.py`
   - Click "ADD TARGET IMAGES"
   - Select image files
   - Faces are detected and added to database

3. **Monitoring:**
   - System detects and tracks faces in real-time
   - When target persons are detected, alerts are triggered
   - Press "START RECORDING" to record video clips
   - Click video viewer to pause/resume

4. **Pre-recorded Video Processing:**
   ```bash
   # Process a video file
   python img-search.py --prerecorded video_filename
   ```

### Workflow 3: Video Processing Pipeline

1. Record videos:
   ```bash
   python record_video.py -o video1
   ```

2. Process videos:
   ```bash
   python img-search.py --prerecorded video1
   ```

3. Videos with detections saved to `matched_videos/`

## Configuration

### Text Search Settings

Default settings in `text-search.py`:
- Confidence Threshold: 0.25
- IoU Threshold: 0.7
- Image Size: 640x640

Modify in `setup_yoloe()` function:
```python
yoloe = setup_yoloe(prompt, confidence=0.25, iou=0.7)
```

### Image Search Settings

Access via GUI:
- **SYSTEM CONFIG**: Adjust overlay settings, detection parameters
- **CAMERA SETUP**: Change resolution (720p, 1080p, 2k, 4k), camera source

## Face Database

The face database is located in `assets/db/`:
- Each person has their own subdirectory
- Face images are saved as `.jpg` files
- Embeddings are saved as `.embed` files
- Database automatically loads on startup

**Adding faces:**
1. Use GUI "ADD TARGET IMAGES" button
2. Or capture photos using `capture_photo.py`
3. Process them through the GUI

## Troubleshooting

### Camera Issues

```bash
# List available cameras
python capture_photo.py --list-cameras

# Use specific camera
python img-search.py  # Uses /dev/video0 by default
```

### Model Loading Errors

**Text Search:**
- Verify `models/` directory contains model files
- Check model paths in `YoloE.py`

**Image Search:**
- Ensure `models-img-search/` directory exists with models
- Check MXFace initialization in `tracker.py`

### Permission Issues

Ensure write permissions for:
- `targets/` - Photo captures
- `videos/` - Video recordings
- `matched_videos/` - Recorded clips
- `assets/db/` - Face database

### Performance Optimization

- Use `--no-preview` for photo/video capture without display
- Lower video resolution for faster processing
- Close other applications using the camera
- Ensure adequate lighting for face detection

## Dependencies

Core requirements (from `requirements.txt`):
```
opencv-python>=4.8.0
numpy>=1.24.0
torch>=2.0.0
torchvision>=0.15.0
ultralytics>=8.0.0
Pillow>=9.5.0
matplotlib>=3.7.0
onnx>=1.14.0
PySide6==6.9.1
lap==0.5.12
```

## Technical Details

### Text Detection (YoloE)
- Uses YoloE for segmentation and object detection
- MobileCLIP for text embeddings
- Real-time processing with configurable thresholds

### Face Recognition (MXFace)
- Deep learning-based face detection and recognition
- BYTETracker for multi-object tracking
- Cosine similarity for face matching
- Threaded detection and recognition pipelines

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## License

This project uses:
- YoloE model and Ultralytics YOLO
- Memryx Neural Compiler
- BYTETracker

Please refer to their respective licenses for usage terms.

## Support

For issues related to:
- **YoloE Model**: Check [Ultralytics YOLO documentation](https://docs.ultralytics.com/)
- **Memryx Neural Compiler**: Visit [Memryx Developer Portal](https://developer.memryx.com/)
- **Application Issues**: Open an issue in this repository
