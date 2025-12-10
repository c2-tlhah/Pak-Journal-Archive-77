"""
Test script for politician classification functionality
"""
import os
import sys
import logging
import json

# Add backend directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from utils.politician_classifier import PoliticianClassifier, get_classifier
from database.db_config import init_db_pool, test_db_connection
from database.video_models import PoliticianClassification

# Configure logging
logging.basicConfig(level=logging.INFO, format='[%(levelname)s] %(message)s')
logger = logging.getLogger(__name__)

def test_classifier_initialization():
    """Test classifier initialization"""
    logger.info("Testing classifier initialization...")

    try:
        # Test with default model path
        classifier = get_classifier()
        logger.info("✓ Classifier initialized successfully")
        return True
    except Exception as e:
        logger.error(f"✗ Classifier initialization failed: {e}")
        return False

def test_database_connection():
    """Test database connection"""
    logger.info("Testing database connection...")

    try:
        if init_db_pool() and test_db_connection():
            logger.info("✓ Database connected successfully")
            return True
        else:
            logger.error("✗ Database connection failed")
            return False
    except Exception as e:
        logger.error(f"✗ Database connection error: {e}")
        return False

def test_video_processing():
    """Test video processing with a sample video"""
    logger.info("Testing video processing...")

    # Look for a sample video in uploads directory
    uploads_dir = os.path.join(os.path.dirname(__file__), '..', 'uploads')
    video_files = [f for f in os.listdir(uploads_dir) if f.endswith(('.mp4', '.avi', '.mov'))]

    if not video_files:
        logger.warning("No video files found in uploads directory. Skipping video processing test.")
        return True

    video_path = os.path.join(uploads_dir, video_files[0])
    logger.info(f"Testing with video: {video_path}")

    try:
        classifier = get_classifier()

        # Test frame extraction
        frames = classifier.extract_frames(video_path, num_frames=5)
        logger.info(f"✓ Extracted {len(frames)} frames")

        # Test classification on first frame
        if frames:
            result = classifier.classify_frame(frames[0][0])
            logger.info(f"✓ Classification result: {result['politician_name']} ({result['confidence_score']:.1f}%)")

        return True

    except Exception as e:
        logger.error(f"✗ Video processing test failed: {e}")
        return False

def test_database_operations():
    """Test database operations for politician classifications"""
    logger.info("Testing database operations...")

    try:
        # Test creating a classification record
        test_video_id = "00000000-0000-0000-0000-000000000001"
        test_user_id = "00000000-0000-0000-0000-000000000002"

        classification_id = PoliticianClassification.create_classification(
            video_id=test_video_id,
            user_id=test_user_id,
            politician_name="Test Politician",
            confidence_score=0.85,
            frame_number=1,
            frame_timestamp=5.0,
            model_version="test-v1",
            classification_data={"test": True},
            status="completed"
        )

        if classification_id:
            logger.info(f"✓ Created test classification: {classification_id}")

            # Test retrieving classifications
            classifications = PoliticianClassification.get_by_video_id(test_video_id)
            logger.info(f"✓ Retrieved {len(classifications)} classifications")

            # Test getting stats
            stats = PoliticianClassification.get_politician_stats(test_video_id)
            logger.info(f"✓ Got stats: {stats}")

            # Clean up test data
            PoliticianClassification.delete_by_video_id(test_video_id)
            logger.info("✓ Cleaned up test data")

            return True
        else:
            logger.error("✗ Failed to create test classification")
            return False

    except Exception as e:
        logger.error(f"✗ Database operations test failed: {e}")
        return False

def main():
    """Run all tests"""
    logger.info("="*60)
    logger.info("Politician Classification System Test")
    logger.info("="*60)

    tests = [
        ("Database Connection", test_database_connection),
        ("Classifier Initialization", test_classifier_initialization),
        ("Video Processing", test_video_processing),
        ("Database Operations", test_database_operations),
    ]

    results = []
    for test_name, test_func in tests:
        logger.info(f"\n--- {test_name} ---")
        success = test_func()
        results.append((test_name, success))

    logger.info("\n" + "="*60)
    logger.info("TEST RESULTS SUMMARY")
    logger.info("="*60)

    all_passed = True
    for test_name, success in results:
        status = "✓ PASS" if success else "✗ FAIL"
        logger.info(f"{status} - {test_name}")
        if not success:
            all_passed = False

    logger.info("="*60)
    if all_passed:
        logger.info("🎉 ALL TESTS PASSED!")
        return 0
    else:
        logger.error("❌ SOME TESTS FAILED!")
        return 1

if __name__ == "__main__":
    sys.exit(main())