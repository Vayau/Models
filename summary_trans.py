import re
from deep_translator import GoogleTranslator


class EnglishToMalayalamTranslator:
    
    def __init__(self):
        self.translator = GoogleTranslator(source='en', target='ml')
    
    def protect_links(self, text):
        link_pattern = re.compile(r'https?://[^\s]+')
        links = []
        
        def replacer(match):
            links.append(match.group(0))
            return f" URLLINK{len(links)-1} "
        
        protected_text = link_pattern.sub(replacer, text)
        return protected_text, links
    
    def restore_links(self, text, links):
        for i, link in enumerate(links):
            placeholder = f" URLLINK{i} "
            text = text.replace(placeholder, link)
        return text
    
    def translate_text(self, text, chunk_size=4000):
        if not text or not text.strip():
            return ""
        
        # Extract URLs first
        url_pattern = re.compile(r'https?://[^\s]+')
        urls = url_pattern.findall(text)
        
        # Remove URLs from text before translation
        text_without_urls = url_pattern.sub('', text).strip()
        
        # If text is small, translate directly
        if len(text_without_urls) <= chunk_size:
            translated_text = self.translator.translate(text_without_urls)
        else:
            # Split into chunks for large texts
            chunks = self._split_text_into_chunks(text_without_urls, chunk_size)
            translated_chunks = []
            
            for chunk in chunks:
                if chunk.strip():
                    translated_chunk = self.translator.translate(chunk)
                    translated_chunks.append(translated_chunk)
            
            translated_text = ' '.join(translated_chunks)
        
        # Add URLs back at the end
        if urls:
            translated_text += ' ' + ' '.join(urls)
        
        return translated_text
    
    def _split_text_into_chunks(self, text, chunk_size):
        # Split by sentences first to maintain meaning
        sentences = re.split(r'(?<=[.!?])\s+', text)
        chunks = []
        current_chunk = ""
        
        for sentence in sentences:
            # If adding this sentence exceeds chunk size
            if len(current_chunk) + len(sentence) + 1 > chunk_size:
                if current_chunk:
                    chunks.append(current_chunk.strip())
                    current_chunk = sentence
                else:
                    # Single sentence is too long, split by words
                    words = sentence.split()
                    for word in words:
                        if len(current_chunk) + len(word) + 1 > chunk_size:
                            if current_chunk:
                                chunks.append(current_chunk.strip())
                                current_chunk = word
                            else:
                                # Single word is too long, just add it
                                chunks.append(word)
                        else:
                            current_chunk += " " + word if current_chunk else word
            else:
                current_chunk += " " + sentence if current_chunk else sentence
        
        # Add remaining chunk
        if current_chunk:
            chunks.append(current_chunk.strip())
        
        return chunks
    
    def translate_sentence(self, sentence):
        if not sentence or not sentence.strip():
            return ""
        
        return self.translator.translate(sentence)


def main():
    translator = EnglishToMalayalamTranslator()
    
    english_text = "Hello! This is a sample text to demonstrate the translation from English to Malayalam. "    
    try:
        malayalam_text = translator.translate_text(english_text)
        print(malayalam_text)
    except Exception as e:
        print(f"Translation error: {e}")


if __name__ == "__main__":
    main()
