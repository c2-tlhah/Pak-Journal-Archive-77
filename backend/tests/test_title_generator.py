"""
Test title generation functionality
"""
import sys
sys.path.append('.')

from utils.title_generator import generate_video_title

# Test cases
test_transcripts = [
    "اسلام آباد میں آج موسم بہت خوشگوار ہے۔ لوگ پارکوں میں گھوم رہے ہیں اور کھیل رہے ہیں۔",
    "وزیر اعظم نے آج قومی اسمبلی میں تقریر کی۔ انہوں نے معاشی بہتری کے لیے نئے منصوبے پیش کیے۔",
    "This is a test of the emergency broadcast system. This is only a test.",
    "Breaking news: Major development in political situation today.",
]

def test_title_generation():
    print("Testing Title Generation...\n")
    
    for i, transcript in enumerate(test_transcripts, 1):
        print(f"Test {i}:")
        print(f"Transcript: {transcript[:100]}...")
        title = generate_video_title(transcript)
        print(f"Generated Title: {title}")
        print("-" * 60)
        print()

if __name__ == "__main__":
    test_title_generation()
