"""
Politician Classification Module for Video Analysis
Uses ResNet-18 CNN model trained on Pakistani politicians dataset
"""
import torch
import torch.nn as nn
from torchvision import models, transforms
from PIL import Image
import cv2
import numpy as np
import os
import logging
from database.video_models import PoliticianClassification, Video
import uuid

logger = logging.getLogger(__name__)

class PoliticianClassifier:
    """
    Handles video frame extraction and politician classification using trained ResNet-18 model
    """

    def __init__(self, model_path="best_politician_resnet.pth"):
        """
        Initialize the classifier with the trained model

        Args:
            model_path: Path to the saved model weights
        """
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.model_path = model_path
        self.model = None
        self.class_names = [
            "Imran Khan", "Nawaz Sharif", "Asif Ali Zardari", "Bilawal Bhutto",
            "Maryam Nawaz", "Shahbaz Sharif", "Fawad Chaudhry", "Pervez Musharraf",
            "Benazir Bhutto", "Altaf Hussain"
        ]  # Update these based on your actual classes

        # Image preprocessing transform (same as training)
        self.transform = transforms.Compose([
            transforms.Resize((224, 224)),
            transforms.ToTensor(),
            transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225])
        ])

        self._load_model()

    def _load_model(self):
        """Load the trained ResNet-18 model"""
        try:
            logger.info(f"Loading politician classification model from {self.model_path}")

            # Initialize ResNet-18 architecture
            self.model = models.resnet18(weights=None)
            num_ftrs = self.model.fc.in_features
            self.model.fc = nn.Linear(num_ftrs, len(self.class_names))
            self.model.load_state_dict(torch.load(self.model_path, map_location=self.device))
            self.model.to(self.device)
            self.model.eval()

            logger.info("✓ Politician classification model loaded successfully")
            logger.info(f"✓ Using device: {self.device}")
            logger.info(f"✓ Classes: {self.class_names}")

        except Exception as e:
            logger.error(f"✗ Failed to load politician classification model: {str(e)}")
            raise e

    def extract_frames(self, video_path, num_frames=10):
        """
        Extract evenly spaced frames from video

        Args:
            video_path: Path to the video file
            num_frames: Number of frames to extract

        Returns:
            list: List of (frame_image, timestamp) tuples
        """
        try:
            logger.info(f"Extracting {num_frames} frames from video: {video_path}")

            # Open video
            cap = cv2.VideoCapture(video_path)
            if not cap.isOpened():
                raise ValueError(f"Could not open video file: {video_path}")

            # Get video properties
            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            fps = cap.get(cv2.CAP_PROP_FPS)
            duration = total_frames / fps if fps > 0 else 0

            logger.info(f"Video info: {total_frames} frames, {fps:.1f} FPS, {duration:.1f}s duration")

            frames_data = []

            # Calculate frame indices to extract (evenly spaced)
            if total_frames <= num_frames:
                # If video is short, take all frames
                frame_indices = list(range(total_frames))
            else:
                # Evenly distribute frames across the video
                frame_indices = [int(i * (total_frames - 1) / (num_frames - 1)) for i in range(num_frames)]

            for frame_idx in frame_indices:
                # Seek to frame
                cap.set(cv2.CAP_PROP_POS_FRAMES, frame_idx)
                ret, frame = cap.read()

                if ret:
                    # Convert BGR to RGB
                    frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

                    # Convert to PIL Image
                    pil_image = Image.fromarray(frame_rgb)

                    # Calculate timestamp
                    timestamp = frame_idx / fps if fps > 0 else 0

                    frames_data.append((pil_image, timestamp, frame_idx))

                    logger.info(f"✓ Extracted frame {len(frames_data)}/{num_frames} at {timestamp:.1f}s")
                else:
                    logger.warning(f"✗ Failed to read frame {frame_idx}")

            cap.release()

            if len(frames_data) == 0:
                raise ValueError("No frames could be extracted from the video")

            logger.info(f"✓ Successfully extracted {len(frames_data)} frames")
            return frames_data

        except Exception as e:
            logger.error(f"✗ Failed to extract frames: {str(e)}")
            raise e

    def classify_frame(self, frame_image):
        """
        Classify a single frame using the trained model

        Args:
            frame_image: PIL Image of the frame

        Returns:
            dict: Classification result with politician name and confidence
        """
        try:
            # Preprocess image
            input_tensor = self.transform(frame_image).unsqueeze(0).to(self.device)

            # Make prediction
            with torch.no_grad():
                outputs = self.model(input_tensor)
                probabilities = torch.nn.functional.softmax(outputs[0], dim=0)

                # Get top prediction
                confidence, predicted_idx = torch.max(probabilities, 0)

            politician_name = self.class_names[predicted_idx.item()]
            confidence_score = confidence.item()

            logger.info(f"✓ Classified: {politician_name} ({confidence_score:.1f}%)")

            return {
                'politician_name': politician_name,
                'confidence_score': confidence_score,
                'predicted_class': predicted_idx.item(),
                'probabilities': probabilities.cpu().numpy().tolist()
            }

        except Exception as e:
            logger.error(f"✗ Failed to classify frame: {str(e)}")
            raise e

    def classify_video(self, video_path, video_id, user_id, num_frames=10):
        """
        Extract frames from video and classify politicians in each frame

        Args:
            video_path: Path to the video file
            video_id: UUID of the video in database
            user_id: UUID of the user
            num_frames: Number of frames to analyze

        Returns:
            list: List of classification results
        """
        try:
            logger.info(f"[Video {video_id}] Starting politician classification")
            logger.info(f"[Video {video_id}] Video path: {video_path}")

            # Extract frames
            frames_data = self.extract_frames(video_path, num_frames)

            # Classify each frame
            classifications = []

            for frame_num, (frame_image, timestamp, frame_idx) in enumerate(frames_data, 1):
                logger.info(f"[Video {video_id}] Classifying frame {frame_num}/{len(frames_data)}")

                # Classify the frame
                result = self.classify_frame(frame_image)

                # Create classification record
                classification_data = {
                    'video_id': video_id,
                    'user_id': user_id,
                    'politician_name': result['politician_name'],
                    'confidence_score': result['confidence_score'],
                    'frame_number': frame_num,
                    'frame_timestamp': timestamp,
                    'model_version': 'resnet18-v1',
                    'classification_data': {
                        'predicted_class': result['predicted_class'],
                        'probabilities': result['probabilities'],
                        'frame_index': frame_idx,
                        'total_frames': len(frames_data)
                    },
                    'status': 'completed'
                }

                # Save to database
                classification = PoliticianClassification.create_classification(**classification_data)
                classifications.append(classification)

                logger.info(f"[Video {video_id}] ✓ Saved classification for frame {frame_num}")

            logger.info(f"[Video {video_id}] ✓ Completed classification of {len(classifications)} frames")
            return classifications

        except Exception as e:
            logger.error(f"[Video {video_id}] ✗ Classification failed: {str(e)}")

            # Create failed classification record
            try:
                PoliticianClassification.create_classification(
                    video_id=video_id,
                    user_id=user_id,
                    politician_name='unknown',
                    confidence_score=0.0,
                    frame_number=0,
                    status='failed',
                    classification_data={'error': str(e)}
                )
            except Exception as db_error:
                logger.error(f"[Video {video_id}] ✗ Failed to save error record: {str(db_error)}")

            raise e

    def get_video_classifications(self, video_id):
        """
        Get all classifications for a specific video

        Args:
            video_id: UUID of the video

        Returns:
            list: List of classification records
        """
        try:
            return PoliticianClassification.get_by_video_id(video_id)
        except Exception as e:
            logger.error(f"Failed to get classifications for video {video_id}: {str(e)}")
            return []

    def get_politician_summary(self, video_id):
        """
        Get a summary of politicians detected in the video

        Args:
            video_id: UUID of the video

        Returns:
            dict: Summary with politician counts and average confidence
        """
        try:
            classifications = self.get_video_classifications(video_id)

            if not classifications:
                return {'politicians': [], 'total_frames': 0}

            # Group by politician
            politician_stats = {}
            for cls in classifications:
                name = cls['politician_name']
                if name not in politician_stats:
                    politician_stats[name] = {
                        'count': 0,
                        'total_confidence': 0.0,
                        'frames': []
                    }

                politician_stats[name]['count'] += 1
                politician_stats[name]['total_confidence'] += cls['confidence_score']
                politician_stats[name]['frames'].append({
                    'frame_number': cls['frame_number'],
                    'timestamp': cls['frame_timestamp'],
                    'confidence': cls['confidence_score']
                })

            # Calculate averages
            summary = []
            for name, stats in politician_stats.items():
                summary.append({
                    'politician_name': name,
                    'frame_count': stats['count'],
                    'average_confidence': stats['total_confidence'] / stats['count'],
                    'frames': stats['frames']
                })

            # Sort by frame count (most detected first)
            summary.sort(key=lambda x: x['frame_count'], reverse=True)

            return {
                'politicians': summary,
                'total_frames': len(classifications)
            }

        except Exception as e:
            logger.error(f"Failed to get politician summary for video {video_id}: {str(e)}")
            return {'politicians': [], 'total_frames': 0}


# Global classifier instance
_classifier_instance = None

def get_classifier(model_path="best_politician_resnet.pth"):
    """
    Get or create the global classifier instance

    Args:
        model_path: Path to the model weights

    Returns:
        PoliticianClassifier: The classifier instance
    """
    global _classifier_instance
    if _classifier_instance is None:
        _classifier_instance = PoliticianClassifier(model_path)
    return _classifier_instance

def classify_video_politicians(video_path, video_id, user_id, model_path="best_politician_resnet.pth"):
    """
    Convenience function to classify politicians in a video

    Args:
        video_path: Path to the video file
        video_id: UUID of the video
        user_id: UUID of the user
        model_path: Path to model weights

    Returns:
        list: Classification results
    """
    classifier = get_classifier(model_path)
    return classifier.classify_video(video_path, video_id, user_id)