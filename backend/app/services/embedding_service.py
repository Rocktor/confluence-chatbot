from sqlalchemy.orm import Session
from app.models.orm import DocumentChunk, ConfluencePage
from app.services.azure_openai_service import AzureOpenAIService
from app.services.document_processor import DocumentProcessor
from typing import List, Dict
import json

class EmbeddingService:
    def __init__(self, db: Session):
        self.db = db
        self.openai_service = AzureOpenAIService()
        self.document_processor = DocumentProcessor()

    async def process_and_store_page(self, page_id: int, content: str, metadata: dict):
        """Process page content and store embeddings"""
        # Delete existing chunks
        self.db.query(DocumentChunk).filter(DocumentChunk.page_id == page_id).delete()

        # Chunk the content
        chunks = self.document_processor.chunk_text(content)

        # Create embeddings and store
        for idx, chunk in enumerate(chunks):
            embedding = await self.openai_service.create_embedding(chunk)

            chunk_record = DocumentChunk(
                page_id=page_id,
                chunk_index=idx,
                content=chunk,
                embedding=embedding,
                metadata=json.dumps(metadata)
            )
            self.db.add(chunk_record)

        self.db.commit()

    async def search_similar_chunks(
        self,
        query: str,
        limit: int = 5,
        similarity_threshold: float = 0.7
    ) -> List[Dict]:
        """Search for similar document chunks"""
        # Create query embedding
        query_embedding = await self.openai_service.create_embedding(query)

        # Vector similarity search using pgvector
        query = f"""
            SELECT
                dc.id,
                dc.content,
                dc.metadata,
                cp.title,
                cp.page_id,
                1 - (dc.embedding <=> CAST(:embedding AS vector)) as similarity
            FROM document_chunks dc
            JOIN confluence_pages cp ON dc.page_id = cp.id
            WHERE 1 - (dc.embedding <=> CAST(:embedding AS vector)) > :threshold
            ORDER BY dc.embedding <=> CAST(:embedding AS vector)
            LIMIT :limit
        """

        result = self.db.execute(
            query,
            {
                "embedding": str(query_embedding),
                "threshold": similarity_threshold,
                "limit": limit
            }
        )

        return [
            {
                "id": row[0],
                "content": row[1],
                "metadata": json.loads(row[2]) if row[2] else {},
                "page_title": row[3],
                "page_id": row[4],
                "similarity": row[5]
            }
            for row in result
        ]
