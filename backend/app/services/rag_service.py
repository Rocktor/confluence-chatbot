from sqlalchemy.orm import Session
from app.services.embedding_service import EmbeddingService
from app.services.azure_openai_service import AzureOpenAIService
from typing import List, Dict

class RAGService:
    def __init__(self, db: Session):
        self.db = db
        self.embedding_service = EmbeddingService(db)
        self.openai_service = AzureOpenAIService()

    async def query_documents(
        self,
        query: str,
        top_k: int = 5,
        similarity_threshold: float = 0.7
    ) -> Dict:
        """Query documents using RAG"""
        # Search similar chunks
        similar_chunks = await self.embedding_service.search_similar_chunks(
            query,
            limit=top_k,
            similarity_threshold=similarity_threshold
        )

        if not similar_chunks:
            return {
                "answer": "抱歉，我在文档中没有找到相关信息。",
                "sources": []
            }

        # Build context from chunks
        context = self._build_context(similar_chunks)

        # Generate answer
        answer = await self._generate_answer(query, context)

        # Extract sources
        sources = self._extract_sources(similar_chunks)

        return {
            "answer": answer,
            "sources": sources,
            "chunks": similar_chunks
        }

    def _build_context(self, chunks: List[Dict]) -> str:
        """Build context from document chunks"""
        context_parts = []
        for idx, chunk in enumerate(chunks, 1):
            context_parts.append(
                f"[文档{idx}] {chunk['page_title']}\n{chunk['content']}\n"
            )
        return "\n".join(context_parts)

    async def _generate_answer(self, query: str, context: str) -> str:
        """Generate answer using LLM"""
        system_prompt = """你是一个专业的文档助手。基于提供的文档内容回答用户的问题。

规则：
1. 只使用提供的文档内容回答问题
2. 如果文档中没有相关信息，明确告知用户
3. 回答要准确、简洁、专业
4. 可以引用文档编号（如[文档1]）来标注信息来源
"""

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"文档内容：\n{context}\n\n问题：{query}"}
        ]

        answer = await self.openai_service.chat_completion(messages)
        return answer

    def _extract_sources(self, chunks: List[Dict]) -> List[Dict]:
        """Extract source information"""
        sources = []
        seen_pages = set()

        for chunk in chunks:
            page_id = chunk['page_id']
            if page_id not in seen_pages:
                sources.append({
                    "page_id": page_id,
                    "title": chunk['page_title'],
                    "similarity": chunk['similarity']
                })
                seen_pages.add(page_id)

        return sources
