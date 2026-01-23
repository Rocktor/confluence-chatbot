from typing import List
import re

class DocumentProcessor:
    def __init__(self, chunk_size: int = 500, chunk_overlap: int = 100):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

    def chunk_text(self, text: str) -> List[str]:
        """Split text into chunks"""
        # Split by sentences
        sentences = re.split(r'(?<=[.!?])\s+', text)

        chunks = []
        current_chunk = ""
        current_size = 0

        for sentence in sentences:
            sentence_size = len(sentence.split())

            if current_size + sentence_size > self.chunk_size and current_chunk:
                chunks.append(current_chunk.strip())

                # Create overlap
                overlap_text = " ".join(current_chunk.split()[-self.chunk_overlap:])
                current_chunk = overlap_text + " " + sentence
                current_size = len(current_chunk.split())
            else:
                current_chunk += " " + sentence
                current_size += sentence_size

        if current_chunk:
            chunks.append(current_chunk.strip())

        return chunks

    def extract_metadata(self, page_data: dict) -> dict:
        """Extract metadata from Confluence page"""
        return {
            "page_id": page_data.get("id"),
            "title": page_data.get("title"),
            "space_key": page_data.get("space", {}).get("key"),
            "version": page_data.get("version", {}).get("number"),
            "last_modified": page_data.get("version", {}).get("when")
        }
