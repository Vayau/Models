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
    
    def translate_text(self, text):
        if not text or not text.strip():
            return ""
        
        # Extract URLs first
        url_pattern = re.compile(r'https?://[^\s]+')
        urls = url_pattern.findall(text)
        
        # Remove URLs from text before translation
        text_without_urls = url_pattern.sub('', text).strip()
        
        # Translate the text without URLs
        translated_text = self.translator.translate(text_without_urls)
        
        # Add URLs back at the end
        if urls:
            translated_text += ' ' + ' '.join(urls)
        
        return translated_text
    
    def translate_sentence(self, sentence):
        if not sentence or not sentence.strip():
            return ""
        
        return self.translator.translate(sentence)


def main():
    translator = EnglishToMalayalamTranslator()
    
    english_text = "In a forgotten town stood an old clockmaker’s shop where Arun Verma kept hundreds of ticking clocks, each tied to a person’s life. When a curious boy named Rishi wandered in, he learned the unsettling truth — that one of the clocks, ticking faster than the rest, was his own. Arun explained that some lives ran quicker than others, but the gift of knowing gave him a choice: to waste time or to live fully. Rishi walked out with his heart racing, suddenly aware that every smile, every word, every small act of courage mattered, while behind him, the old clockmaker wound his own slowly ticking clock, content with the rhythm of time. https://leetcode.com/u/anshu__15/"
    
    try:
        malayalam_text = translator.translate_text(english_text)
        print(malayalam_text)
    except Exception as e:
        print(f"Translation error: {e}")


if __name__ == "__main__":
    main()
