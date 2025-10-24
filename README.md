# YoloE Text-Searching Application

A real-time object detection application using YoloE with natural language prompts. This application allows you to detect complex object combinations using natural language descriptions like "man wearing glasses" or "car with person inside".

## Features

- **Natural Language Prompts**: Use descriptive phrases instead of individual object classes
- **Real-time Detection**: Live camera feed with object detection and segmentation
- **Image Saving**: Press 's' to save detected frames to the `snippets/` folder
- **Customizable Detection**: Adjust confidence and IoU thresholds

## Installation

### Prerequisites

- Python 3.8 or higher
- OpenCV
- PyTorch
- Ultralytics YOLO
- Memryx Neural Compiler

### Step 1: Install Dependencies

```bash
pip install -r requirements.txt
```

### Step 2: Download and Prepare the Pre-compiled DFP

To download and unzip the precompiled DFPs, use the following commands:

```bash
wget https://developer.memryx.com/example_files/YoloE-v8s-seg_640_640_3_onnx.zip
mkdir -p models
unzip YoloE-v8s-seg_640_640_3_onnx.zip -d models
```

This will create the necessary model files in the `models/` directory:
- `yoloe-v8s-seg_post.onnx` - Post-processing model
- `yoloe-v8s-seg.dfp` - Pre-compiled DFP file

### Step 3: Verify Installation

Ensure your directory structure looks like this:

```
text-searching/
├── main.py
├── modules/
│   ├── __init__.py
│   └── YoloE.py
├── models/
│   ├── yoloe-v8s-seg_post.onnx
│   └── yoloe-v8s-seg.dfp
├── requirements.txt
└── README.md
```

## Usage

### Basic Usage

Run the application with a natural language prompt:

```bash
python main.py --search "man wearing glasses"
```

### Examples

```bash
# Detect men wearing glasses
python main.py --search "man wearing glasses"

# Detect cars with people inside
python main.py --search "car with person inside"

# Detect dogs and cats together
python main.py --search "dog and cat"

# Detect people holding bottles
python main.py --search "person holding bottle"
```

### Controls

- **Press 's'**: Save current frame to `snippets/` folder
- **Press 'q' or ESC**: Quit the application

### Output

- Detected objects will be highlighted with bounding boxes and segmentation masks
- Saved images will be stored in the `snippets/` folder with timestamps
- Console output shows detection progress and statistics

## How It Works

1. **Text Embedding**: The natural language prompt is converted to text embeddings using MobileCLIP
2. **Object Detection**: YoloE processes the camera feed and detects objects matching the prompt
3. **Segmentation**: Provides pixel-level segmentation masks for detected objects
4. **Real-time Processing**: Continuously processes video frames with customizable confidence thresholds

## Configuration

The application uses the following default settings:
- **Confidence Threshold**: 0.25
- **IoU Threshold**: 0.7
- **Image Size**: 640x640
- **Camera Source**: Default camera (0)

## Troubleshooting

### Common Issues

1. **Permission Denied Error**: Make sure you have write permissions in the current directory for the `snippets/` folder
2. **Camera Not Found**: Ensure your camera is connected and not being used by another application
3. **Model Loading Error**: Verify that the model files are correctly placed in the `models/` directory

### Performance Tips

- Close other applications using the camera
- Ensure good lighting conditions for better detection
- Use specific, clear prompts for better accuracy

## File Structure

```
text-searching/
├── main.py                 # Main application script
├── modules/
│   ├── __init__.py        # Module initialization
│   └── YoloE.py          # YoloE implementation
├── models/                # Model files (downloaded)
├── snippets/              # Saved images (generated)
├── requirements.txt       # Python dependencies
├── .gitignore            # Git ignore rules
└── README.md             # This file
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## License

This project uses the YoloE model and Memryx Neural Compiler. Please refer to their respective licenses for usage terms.

## Support

For issues related to:
- **YoloE Model**: Check the [Ultralytics YOLO documentation](https://docs.ultralytics.com/)
- **Memryx Neural Compiler**: Visit [Memryx Developer Portal](https://developer.memryx.com/)
- **Application Issues**: Open an issue in this repository
