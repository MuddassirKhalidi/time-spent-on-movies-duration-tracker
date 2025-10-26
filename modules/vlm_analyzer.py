import os
import time
import google.generativeai as genai


class VideoAnalyzer:
    """
    A sophisticated video analysis system that processes and understands video content.
    """
    
    def __init__(self, model_name: str = "gemini-2.5-flash"):
        """
        Initialize the video analyzer.
        
        Args:
            model_name: The AI model to use for analysis
        """
        api_key = "XXXXXXXXXXXXXXXXXXXX" #Change to your api key
        self._configure_service(api_key)
        self._model_name = model_name
        self._uploaded_resource = None
        
    def _configure_service(self, api_key: str) -> None:
        """Configure the underlying AI service."""
        genai.configure(api_key=api_key)
    
    def load_video(self, video_path: str, polling_interval: int = 2) -> None:
        """
        Load and prepare a video file for analysis.
        
        Args:
            video_path: Path to the video file
            polling_interval: Seconds to wait between status checks
            
        Raises:
            FileNotFoundError: If the video file doesn't exist
            VideoProcessingError: If video processing fails
        """
        if not os.path.exists(video_path):
            raise FileNotFoundError(f"Video file not found: {video_path}")
        
        print(f"Loading video: {video_path}")
        self._uploaded_resource = genai.upload_file(video_path)
        
        print(f"Video uploaded successfully. Processing...")
        self._wait_for_processing(polling_interval)
        print("Video is ready for analysis.")
    
    def _wait_for_processing(self, polling_interval: int) -> None:
        """
        Wait for the video to be fully processed.
        
        Args:
            polling_interval: Seconds to wait between status checks
            
        Raises:
            VideoProcessingError: If processing fails
        """
        while self._uploaded_resource.state.name == "PROCESSING":
            time.sleep(polling_interval)
            self._uploaded_resource = genai.get_file(self._uploaded_resource.name)
        
        if self._uploaded_resource.state.name != "ACTIVE":
            raise VideoProcessingError(
                f"Video processing failed with status: {self._uploaded_resource.state.name}"
            )
    
    def analyze(self, prompt: str = "Explain in detail what happens in the video.") -> str:
        """
        Analyze the loaded video using AI.
        
        Args:
            prompt: The analysis instruction or question about the video
            
        Returns:
            Detailed analysis of the video content
            
        Raises:
            VideoNotLoadedError: If no video has been loaded
        """
        if self._uploaded_resource is None:
            raise VideoNotLoadedError("No video loaded. Call load_video() first.")
        
        print("Analyzing video content...")
        model = genai.GenerativeModel(self._model_name)
        response = model.generate_content([self._uploaded_resource, prompt])
        
        return response.text
    
    def understand(self, question: str) -> str:
        """
        Ask a specific question about the video content.
        
        Args:
            question: Question to ask about the video
            
        Returns:
            Answer based on video analysis
        """
        return self.analyze(question)
    
    def generate_security_report(self) -> str:
        """
        Generate a professional security surveillance report from the video footage.
        Automatically uses face recognition labels if available in the video.
        
        Returns:
            Formatted security report with timestamps, personnel descriptions,
            activities, and any mentioned names
            
        Raises:
            VideoNotLoadedError: If no video has been loaded
        """
        if self._uploaded_resource is None:
            raise VideoNotLoadedError("No video loaded. Call load_video() first.")
        
        prompt = """Analyze this video as CCTV security footage and generate a professional security report.

CRITICAL INSTRUCTIONS FOR NAME USAGE:
- This video contains face recognition labels showing "found [name]" for identified individuals
- Use those actual names naturally throughout the report (e.g., "John Smith enters the room" instead of "Person 1 enters")
- NEVER mention the face recognition system, detection process, or labels themselves (no "identified as", "detected as", "labeled as", "found [name]", etc.)
- NEVER describe technical aspects like "temporarily identified as Unknown" or "inconsistently labeled"
- Write as if the names are simply known facts, not the output of a system
- If someone lacks a name label, use descriptive identifiers (e.g., "Person in blue shirt", "Unidentified individual")
- For multiple people with the same name, distinguish them by physical appearance (e.g., "Ahmed (White Thobe)", "Ahmed (Gray Suit)")

FORMAT YOUR RESPONSE EXACTLY AS FOLLOWS:

SECURITY INCIDENT REPORT
========================

TIMESTAMP ANALYSIS:
-------------------
Provide a chronological breakdown with timestamps (estimate based on video progression):
[00:00-00:15] - [Use actual names naturally, e.g., "Ahmed enters the room and approaches the desk"]
[00:15-00:30] - [Description of what's happening]
(Continue for the entire video duration)

PERSONNEL PRESENT:
--------------------
[List individuals with their names if available, otherwise use descriptive identifiers]
Ahmed Khalil: [Physical description - height estimate, build, clothing, distinguishing features]
Sarah Mohammed: [Physical description]
Person in Blue Jacket: [Physical description if no name available]
(List all individuals observed)

ACTIVITIES OBSERVED:
-------------------
[Detailed description of all actions, movements, and behaviors - use actual names naturally when available]

IDENTIFIERS NOTED:
---------------------------
[List any names visible on ID badges, spoken names, license plates, or other identifying information]
[If none, state "No additional identifiers noted"]

POINTS OF INTEREST:
------------------
[Any suspicious activities, safety concerns, or notable events]

REPORT STATUS: [Complete/Ongoing/Requires Follow-up]

Provide thorough, objective observations suitable for security documentation. Always prioritize using actual names from face recognition over generic labels."""

        print("Generating security surveillance report...")
        model = genai.GenerativeModel(self._model_name)
        response = model.generate_content([self._uploaded_resource, prompt])
        
        return response.text
    
    def track_person_of_interest(self, person_name: str) -> str:
        """
        Generate a focused report tracking a specific person of interest in the video.
        
        Args:
            person_name: The name of the person to track (as it appears in face recognition labels)
            
        Returns:
            Detailed report focused solely on the specified individual's activities
            
        Raises:
            VideoNotLoadedError: If no video has been loaded
        """
        if self._uploaded_resource is None:
            raise VideoNotLoadedError("No video loaded. Call load_video() first.")
        
        prompt = f"""Analyze this video and generate a detailed report focused EXCLUSIVELY on the person named "{person_name}".

CRITICAL INSTRUCTIONS:
- This video contains face recognition labels - look for "found {person_name}" labels to identify the target
- Use the name "{person_name}" naturally throughout the report
- NEVER mention the face recognition system, detection, or labels (no "identified as", "detected via face recognition", "found [name]", etc.)
- NEVER describe technical issues like inconsistent labeling or "Unknown" labels
- Write as if you simply know who {person_name} is
- If multiple people share the same name, distinguish them by appearance (e.g., "{person_name} (White Thobe)", "{person_name} (Blue Suit)")
- Focus only on {person_name}'s activities - mention others only when they interact with {person_name}

FORMAT YOUR RESPONSE EXACTLY AS FOLLOWS:

PERSON OF INTEREST TRACKING REPORT
===================================
Target: {person_name}

PRESENCE CONFIRMATION:
---------------------------
[Confirm if {person_name} appears in the footage - "Present" or "Not observed"]
[If multiple people share this name, note: "Multiple individuals named {person_name} observed"]

APPEARANCE AND DESCRIPTION:
--------------------------
[Detailed physical description of {person_name}]
- Clothing: [Description]
- Distinguishing features: [Features]
- Accessories: [Any visible items]

TIMELINE OF ACTIVITIES:
----------------------
[Chronological breakdown of ONLY {person_name}'s actions]
[00:00-00:15] - {person_name} [specific action]
[00:15-00:30] - {person_name} [specific action]
(Continue for all appearances)

INTERACTIONS:
------------
[List everyone {person_name} interacts with and the nature of interactions]
- Interaction with [Person/Name]: [Description]

LOCATIONS VISITED:
-----------------
[All areas/rooms/locations where {person_name} appears]

OBJECTS HANDLED:
---------------
[Any items {person_name} touches, carries, or interacts with]

DURATION IN FRAME:
-----------------
[Estimate total time {person_name} is visible in the video]
[Note any periods where they leave and re-enter the frame]

BEHAVIORAL NOTES:
----------------
[Observations about {person_name}'s behavior, demeanor, urgency, etc.]

SUMMARY:
--------
[Concise overview of {person_name}'s activities and significance in the footage]

NOTE: This report focuses exclusively on {person_name}. Other individuals are mentioned only in context of their interactions with the target.

Write naturally without mentioning any face recognition technology or detection systems."""

        print(f"Tracking person of interest: {person_name}...")
        model = genai.GenerativeModel(self._model_name)
        response = model.generate_content([self._uploaded_resource, prompt])
        
        return response.text
    
    def get_summary(self) -> str:
        """
        Generate a concise executive summary of the video content.
        
        Returns:
            Brief overview of key events and activities in the video
            
        Raises:
            VideoNotLoadedError: If no video has been loaded
        """
        if self._uploaded_resource is None:
            raise VideoNotLoadedError("No video loaded. Call load_video() first.")
        
        prompt = """Provide a concise executive summary of this video in 3-5 sentences.

IMPORTANT: If the video contains face recognition labels with names, use those actual names naturally in the summary. NEVER mention the face recognition system itself or phrases like "identified as", "detected as", or "labeled as". Write as if the names are simply known.

Focus on:
- Main subject/activity
- Key events or actions
- Overall context and purpose
- Any significant outcomes

Keep it brief and professional."""

        print("Generating summary...")
        model = genai.GenerativeModel(self._model_name)
        response = model.generate_content([self._uploaded_resource, prompt])
        
        return response.text
    
    @property
    def is_ready(self) -> bool:
        """Check if a video is loaded and ready for analysis."""
        return (self._uploaded_resource is not None and 
                self._uploaded_resource.state.name == "ACTIVE")


class VideoProcessingError(Exception):
    """Raised when video processing fails."""
    pass


class VideoNotLoadedError(Exception):
    """Raised when attempting to analyze without loading a video."""
    pass


# Example usage
if __name__ == "__main__":
    # Initialize the analyzer
    analyzer = VideoAnalyzer()
    
    # Load and process a video
    analyzer.load_video("vid.mp4")
    
    # Generate a security report (will use face recognition names if available)
    security_report = analyzer.generate_security_report()
    print("\n" + "="*60)
    print("SECURITY SURVEILLANCE REPORT")
    print("="*60)
    print(security_report)
    
    # Track a specific person of interest
    person_report = analyzer.track_person_of_interest("mio")
    print("\n" + "="*60)
    print("PERSON OF INTEREST REPORT")
    print("="*60)
    print(person_report)
    
    # Get a quick summary
    summary = analyzer.get_summary()
    print("\n" + "="*60)
    print("EXECUTIVE SUMMARY")
    print("="*60)
    print(summary)
