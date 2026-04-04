"""
Title Generator using Translation + LaBSE
1. Translates Urdu transcript to English
2. Uses LaBSE to find the most central/representative sentence
3. Translates the result back to Urdu
"""
import logging
import torch
from sentence_transformers import SentenceTransformer
from deep_translator import GoogleTranslator
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
import re

logger = logging.getLogger(__name__)

class TitleGenerator:
    def __init__(self):
        self.model = None
        self.initialized = False
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        
    def initialize(self):
        """Initialize the sentence embedding model"""
        try:
            logger.info("Loading title generation model (LaBSE)...")
            self.model = SentenceTransformer('sentence-transformers/LaBSE')
            self.model.half()
            self.model.to(self.device)
            self.initialized = True
            logger.info(f"[OK] Title generation model loaded on {self.device}")
        except Exception as e:
            logger.error(f"[FAIL] Failed to load title generation model: {e}")
            self.initialized = False
    
    def generate_title(self, transcript: str, max_length: int = 100) -> str:
        """
        Generate a title by translating to English, finding best sentence, 
        and translating back to Urdu.
        """
        try:
            if not transcript or len(transcript.strip()) < 10:
                return "بغیر عنوان ویڈیو"
            
            if not self.initialized or self.model is None:
                logger.warning("Model not initialized, using fallback")
                return self._fallback_title(transcript)

            # 1. Translate Urdu transcript to English
            # Limit to first 2000 chars to avoid timeouts/limits
            transcript_chunk = transcript[:2000]
            logger.info("Translating transcript to English...")
            
            try:
                english_text = GoogleTranslator(source='auto', target='en').translate(transcript_chunk)
            except Exception as e:
                logger.error(f"Translation to English failed: {e}")
                return self._fallback_title(transcript)

            if not english_text:
                return self._fallback_title(transcript)

            # 2. Split into sentences
            sentences = re.split(r'(?<=[.!?])\s+', english_text)
            sentences = [s.strip() for s in sentences if len(s.strip()) > 20]
            
            if not sentences:
                return self._fallback_title(transcript)
            
            # 3. Find the most representative sentence using LaBSE
            # Encode all sentences
            sentence_embeddings = self.model.encode(sentences)
            
            # Calculate document embedding (mean of sentence embeddings)
            doc_embedding = np.mean(sentence_embeddings, axis=0).reshape(1, -1)
            
            # Calculate similarity of each sentence to the document
            similarities = cosine_similarity(sentence_embeddings, doc_embedding)
            
            # Get index of most similar sentence
            best_idx = np.argmax(similarities)
            best_sentence = sentences[best_idx]
            
            logger.info(f"Selected English title candidate: {best_sentence}")
            
            # 4. Translate back to Urdu
            logger.info("Translating title back to Urdu...")
            urdu_title = GoogleTranslator(source='en', target='ur').translate(best_sentence)
            
            # 5. Cleanup and truncate
            final_title = self._clean_title(urdu_title, max_length)
            
            logger.info(f"[OK] Generated Urdu title: {final_title}")
            return final_title
            
        except Exception as e:
            logger.error(f"[FAIL] Title generation failed: {e}")
            return self._fallback_title(transcript)
    
    def _clean_title(self, title: str, max_length: int) -> str:
        """Clean and format the final Urdu title"""
        if not title:
            return "بغیر عنوان ویڈیو"
            
        # Remove extra whitespace
        title = re.sub(r'\s+', ' ', title).strip()
        
        # Remove common starting filler words in Urdu if needed
        # (Optional, can be expanded)
        
        # Truncate
        if len(title) > max_length:
            title = title[:max_length]
            last_space = title.rfind(' ')
            if last_space > 0:
                title = title[:last_space]
            title += "..."
            
        return title

    def _fallback_title(self, transcript: str) -> str:
        """Simple fallback if translation/AI fails"""
        # Just take the first few words of the original transcript
        words = transcript.split()[:10]
        return " ".join(words) + "..." if words else "بغیر عنوان ویڈیو"
    
    def _clean_text(self, text: str) -> str:
        """Clean text for better summarization"""
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text)
        # Remove special characters but keep Urdu/Arabic script
        text = re.sub(r'[^\w\s\u0600-\u06FF\u0750-\u077F\u08A0-\u08FF]', '', text)
        return text.strip()
    
    def _format_title(self, title: str, max_length: int) -> str:
        """Format and clean the generated title"""
        # Remove quotes if present
        title = title.strip('"\'')
        
        # Capitalize first letter if English
        if title and title[0].isalpha() and ord(title[0]) < 128:
            title = title[0].upper() + title[1:]
        
        # Truncate if too long
        if len(title) > max_length:
            title = title[:max_length].rsplit(' ', 1)[0]
            if not title.endswith('.'):
                title += '...'
        
        return title
    
    def _generate_title_fallback(self, transcript: str, max_length: int) -> str:
        """
        Fallback title generation using simple extraction
        Takes the first sentence or first N words
        """
        try:
            # Clean the text
            cleaned = self._clean_text(transcript)
            
            # Try to extract first sentence
            sentences = re.split(r'[۔.!?]\s+', cleaned)
            if sentences and len(sentences[0]) > 10:
                title = sentences[0]
            else:
                # Take first 10-15 words
                words = cleaned.split()[:12]
                title = ' '.join(words)
            
            # Format and truncate
            title = self._format_title(title, max_length)
            
            # If still too short or empty, use default
            if len(title.strip()) < 5:
                return "Untitled Video"
            
            return title
            
        except Exception as e:
            logger.error(f"[FAIL] Fallback title generation failed: {e}")
            return "Untitled Video"

# Global instance
_title_generator = None

def get_title_generator():
    """Get or create the global title generator instance"""
    global _title_generator
    if _title_generator is None:
        _title_generator = TitleGenerator()
        _title_generator.initialize()
    return _title_generator

def generate_video_title(transcript: str) -> str:
    """
    Convenience function to generate a title from transcript
    
    Args:
        transcript: The full transcript text
        
    Returns:
        Generated title string
    """
    generator = get_title_generator()
    return generator.generate_title(transcript)
