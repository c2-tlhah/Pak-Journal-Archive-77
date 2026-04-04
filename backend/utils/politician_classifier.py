"""
Politician Classification Module for Video Analysis
Uses ResNet-18 CNN model trained on Pakistani politicians dataset
"""
import torch
import torch.nn as nn
import gc
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

    def __init__(self, model_path=r"C:\Users\omerf\pak_politicians_cnn_v2.pth"):
        """
        Initialize the classifier with the trained model

        Args:
            model_path: Path to the saved model weights
        """
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.model_path = model_path
        self.model = None
        # 9 Classes based on the user's notebook configuration
        self.class_names = [
            'Ahmed Sharif', 'Asif Zardari', 'Asim Munir', 
            'Benazir Bhutto', 'Bilawal Bhutto', 'Imran Khan', 
            'Nawaz Sharif', 'Shah Mehmood', 'Shahbaz Sharif'
        ]

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

            logger.info("[OK] Politician classification model loaded successfully")
            logger.info(f"[OK] Using device: {self.device}")
            logger.info(f"[OK] Classes: {self.class_names}")

        except Exception as e:
            logger.error(f"[FAIL] Failed to load politician classification model: {str(e)}")
            raise e

    def extract_frames(self, video_path, interval_seconds=25):
        """
        Extract 1 frame every `interval_seconds` from video

        Args:
            video_path: Path to the video file
            interval_seconds: Interval in seconds between frames

        Returns:
            list: List of (frame_image, timestamp, frame_idx) tuples
        """
        try:
            logger.info(f"Extracting frames every {interval_seconds}s from video: {video_path}")

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
            
            if fps <= 0:
                logger.warning("Invalid FPS, defaulting to 30")
                fps = 30

            frame_interval = int(fps * interval_seconds)
            if frame_interval == 0:
                frame_interval = 1

            # Calculate frame indices to extract
            frame_indices = range(0, total_frames, frame_interval)

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
                    timestamp = frame_idx / fps

                    frames_data.append((pil_image, timestamp, frame_idx))

                    logger.info(f"[OK] Extracted frame at {timestamp:.1f}s")
                else:
                    logger.warning(f"[FAIL] Failed to read frame {frame_idx}")

            cap.release()

            if len(frames_data) == 0:
                logger.warning("No frames extracted, trying to extract at least one frame")
                # Try to extract the first frame if nothing else worked
                cap = cv2.VideoCapture(video_path)
                ret, frame = cap.read()
                if ret:
                     frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                     pil_image = Image.fromarray(frame_rgb)
                     frames_data.append((pil_image, 0.0, 0))
                cap.release()

            logger.info(f"[OK] Successfully extracted {len(frames_data)} frames")
            return frames_data

        except Exception as e:
            logger.error(f"[FAIL] Failed to extract frames: {str(e)}")
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

            logger.info(f"[OK] Classified: {politician_name} ({confidence_score:.1f}%)")

            return {
                'politician_name': politician_name,
                'confidence_score': confidence_score,
                'predicted_class': predicted_idx.item(),
                'probabilities': probabilities.cpu().numpy().tolist()
            }

        except Exception as e:
            logger.error(f"[FAIL] Failed to classify frame: {str(e)}")
            raise e

    def classify_video(self, video_path, video_id, user_id):
        """
        Extract frames from video and classify politicians in each frame.
        Applies majority voting to identify the speaker.

        Args:
            video_path: Path to the video file
            video_id: UUID of the video in database
            user_id: UUID of the user

        Returns:
            list: List of classification results
        """
        try:
            logger.info(f"[Video {video_id}] Starting politician classification")
            logger.info(f"[Video {video_id}] Video path: {video_path}")

            # Extract frames (1 every 10 seconds)
            frames_data = self.extract_frames(video_path, interval_seconds=10)

            # Classify each frame
            classifications = []
            results_for_voting = []

            for frame_num, (frame_image, timestamp, frame_idx) in enumerate(frames_data, 1):
                logger.info(f"[Video {video_id}] Classifying frame {frame_num}/{len(frames_data)}")

                # Classify the frame
                result = self.classify_frame(frame_image)
                
                # Store for voting
                results_for_voting.append(result)

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
                classification_id = PoliticianClassification.create_classification(**classification_data)
                if classification_id:
                    # Add ID to the local dict for return
                    classification_data['id'] = classification_id
                    classifications.append(classification_data)

                logger.info(f"[Video {video_id}] [OK] Saved classification for frame {frame_num}")

            # --- Business Logic: Majority Voting & Threshold ---
            if results_for_voting:
                counts = {}
                confidences = {}

                for res in results_for_voting:
                    name = res['politician_name']
                    score = res['confidence_score']
                    
                    counts[name] = counts.get(name, 0) + 1
                    if name not in confidences:
                        confidences[name] = []
                    confidences[name].append(score)
                
                # Find winner (Most frequent class)
                winner = max(counts, key=counts.get)
                
                # Calculate average confidence for the winner
                avg_confidence = sum(confidences[winner]) / len(confidences[winner])
                
                logger.info(f"[Video {video_id}] Winner: {winner} (Count: {counts[winner]}, Avg Conf: {avg_confidence:.2f})")

                # Apply Confidence Threshold Rule
                final_speaker = winner
                if avg_confidence < 0.20: # 20% threshold
                    final_speaker = "Unknown Speaker"
                    logger.info(f"[Video {video_id}] Confidence too low (< 0.20). Marked as Unknown Speaker.")
                
                # Update Video Record
                Video.update_video_speaker(video_id, final_speaker)
            else:
                logger.warning(f"[Video {video_id}] No frames classified. Cannot identify speaker.")

            logger.info(f"[Video {video_id}] [OK] Completed classification of {len(classifications)} frames")
            return classifications

        except Exception as e:
            logger.error(f"[Video {video_id}] [FAIL] Classification failed: {str(e)}")

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
                logger.error(f"[Video {video_id}] [FAIL] Failed to save error record: {str(db_error)}")

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

def unload_classifier():
    """Free politician classifier from GPU to reclaim VRAM."""
    global _classifier_instance
    if _classifier_instance is not None:
        if _classifier_instance.model is not None:
            del _classifier_instance.model
            _classifier_instance.model = None
        del _classifier_instance
        _classifier_instance = None
    gc.collect()
    if torch.cuda.is_available():
        torch.cuda.empty_cache()
    logger.info("Politician classifier unloaded from VRAM")

def get_classifier(model_path="best_politician_resnet_v2.pth"):
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

def classify_video_politicians(video_path, video_id, user_id, model_path=r"C:\Users\omerf\pak_politicians_cnn_v2.pth"):
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