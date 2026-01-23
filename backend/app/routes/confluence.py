from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.dependencies.database import get_db
from app.middleware.jwt_auth import get_current_user
from app.services.confluence_service import ConfluenceService
from app.services.embedding_service import EmbeddingService
from app.models.schemas import (
    ConfluenceConfigCreate,
    ConfluenceConfigResponse,
    ConfluencePageCreate,
    ConfluencePageUpdate,
    ConfluencePageResponse,
    ConfluenceSyncRequest
)
from app.models.orm import User, ConfluenceConfig, ConfluencePage
from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel
import re

router = APIRouter(prefix="/api/confluence", tags=["confluence"])


class ConfluenceLoadRequest(BaseModel):
    url: str


class ConfluenceTestRequest(BaseModel):
    base_url: str
    email: str
    api_token: Optional[str] = None  # 可选，如果有 config_id 则使用已保存的 token
    space_key: Optional[str] = None
    config_id: Optional[int] = None  # 已有配置的 ID


class WriteBackRequest(BaseModel):
    content: str
    title: Optional[str] = None
    space_key: Optional[str] = None
    parent_id: Optional[str] = None

@router.post("/configs", response_model=ConfluenceConfigResponse)
async def create_config(
    config: ConfluenceConfigCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create Confluence configuration"""
    # Encrypt API token
    encrypted_token = ConfluenceService.encrypt_token(config.api_token)

    # Create config
    confluence_config = ConfluenceConfig(
        user_id=current_user.id,
        base_url=config.base_url,
        email=config.email,
        api_token_encrypted=encrypted_token,
        space_key=config.space_key
    )
    db.add(confluence_config)
    db.commit()
    db.refresh(confluence_config)

    return confluence_config

@router.get("/configs", response_model=List[ConfluenceConfigResponse])
async def get_configs(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get user's Confluence configurations"""
    return db.query(ConfluenceConfig).filter(
        ConfluenceConfig.user_id == current_user.id
    ).all()

@router.post("/pages", response_model=ConfluencePageResponse)
async def create_page(
    page: ConfluencePageCreate,
    config_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create Confluence page"""
    # Get config
    config = db.query(ConfluenceConfig).filter(
        ConfluenceConfig.id == config_id,
        ConfluenceConfig.user_id == current_user.id
    ).first()

    if not config:
        raise HTTPException(status_code=404, detail="Configuration not found")

    # Decrypt token
    api_token = ConfluenceService.decrypt_token(config.api_token_encrypted)

    # Create Confluence service
    confluence = ConfluenceService(config.base_url, config.email, api_token)

    # Convert markdown to HTML
    html_content = confluence.markdown_to_html(page.content)

    # Create page
    result = await confluence.create_page(
        page.space_key,
        page.title,
        html_content,
        page.parent_id
    )

    # Store in database
    confluence_page = ConfluencePage(
        config_id=config_id,
        page_id=result["id"],
        title=result["title"],
        space_key=page.space_key,
        content_markdown=page.content
    )
    db.add(confluence_page)
    db.commit()
    db.refresh(confluence_page)

    return confluence_page

@router.get("/pages/{page_id}", response_model=ConfluencePageResponse)
async def get_page(
    page_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get Confluence page"""
    page = db.query(ConfluencePage).join(ConfluenceConfig).filter(
        ConfluencePage.id == page_id,
        ConfluenceConfig.user_id == current_user.id
    ).first()

    if not page:
        raise HTTPException(status_code=404, detail="Page not found")

    return page

@router.put("/pages/{page_id}", response_model=ConfluencePageResponse)
async def update_page(
    page_id: int,
    page_update: ConfluencePageUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update Confluence page"""
    # Get page
    page = db.query(ConfluencePage).join(ConfluenceConfig).filter(
        ConfluencePage.id == page_id,
        ConfluenceConfig.user_id == current_user.id
    ).first()

    if not page:
        raise HTTPException(status_code=404, detail="Page not found")

    # Get config
    config = page.config
    api_token = ConfluenceService.decrypt_token(config.api_token_encrypted)

    # Create Confluence service
    confluence = ConfluenceService(config.base_url, config.email, api_token)

    # Get current version
    current_page = await confluence.get_page(page.page_id)
    version = current_page["version"]["number"]

    # Update page
    title = page_update.title or page.title
    content = page_update.content or page.content_markdown
    html_content = confluence.markdown_to_html(content)

    await confluence.update_page(page.page_id, title, html_content, version)

    # Update database
    page.title = title
    page.content_markdown = content
    db.commit()
    db.refresh(page)

    return page

@router.delete("/pages/{page_id}")
async def delete_page(
    page_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete Confluence page"""
    # Get page
    page = db.query(ConfluencePage).join(ConfluenceConfig).filter(
        ConfluencePage.id == page_id,
        ConfluenceConfig.user_id == current_user.id
    ).first()

    if not page:
        raise HTTPException(status_code=404, detail="Page not found")

    # Get config
    config = page.config
    api_token = ConfluenceService.decrypt_token(config.api_token_encrypted)

    # Create Confluence service
    confluence = ConfluenceService(config.base_url, config.email, api_token)

    # Delete from Confluence
    await confluence.delete_page(page.page_id)

    # Delete from database
    db.delete(page)
    db.commit()

    return {"success": True}

@router.post("/sync")
async def sync_page(
    sync_request: ConfluenceSyncRequest,
    config_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Sync Confluence page and create embeddings"""
    # Get config
    config = db.query(ConfluenceConfig).filter(
        ConfluenceConfig.id == config_id,
        ConfluenceConfig.user_id == current_user.id
    ).first()

    if not config:
        raise HTTPException(status_code=404, detail="Configuration not found")

    # Extract page ID from URL
    match = re.search(r'/pages/(\d+)', sync_request.page_url)
    if not match:
        raise HTTPException(status_code=400, detail="Invalid page URL")

    page_id_str = match.group(1)

    # Decrypt token
    api_token = ConfluenceService.decrypt_token(config.api_token_encrypted)

    # Create Confluence service
    confluence = ConfluenceService(config.base_url, config.email, api_token)

    # Get page content
    page_data = await confluence.get_page(page_id_str)

    # Convert to markdown
    html_content = page_data["body"]["storage"]["value"]
    markdown_content = confluence.html_to_markdown(html_content)

    # Store or update page
    page = db.query(ConfluencePage).filter(
        ConfluencePage.config_id == config_id,
        ConfluencePage.page_id == page_id_str
    ).first()

    if page:
        page.title = page_data["title"]
        page.content_markdown = markdown_content
        page.last_synced_at = datetime.utcnow()
    else:
        page = ConfluencePage(
            config_id=config_id,
            page_id=page_id_str,
            title=page_data["title"],
            space_key=page_data["space"]["key"],
            content_markdown=markdown_content,
            last_synced_at=datetime.utcnow()
        )
        db.add(page)

    db.commit()
    db.refresh(page)

    # Create embeddings
    embedding_service = EmbeddingService(db)
    metadata = {
        "title": page.title,
        "space_key": page.space_key,
        "page_id": page.page_id
    }
    await embedding_service.process_and_store_page(page.id, markdown_content, metadata)

    return {"success": True, "page_id": page.id}


@router.get("/search")
async def search_confluence(
    q: str = Query(..., min_length=1),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Search Confluence pages"""
    # Get user's active config
    config = db.query(ConfluenceConfig).filter(
        ConfluenceConfig.user_id == current_user.id,
        ConfluenceConfig.is_active == True
    ).first()

    if not config:
        raise HTTPException(status_code=400, detail="No Confluence configuration found")

    api_token = ConfluenceService.decrypt_token(config.api_token_encrypted)
    confluence = ConfluenceService(config.base_url, config.email, api_token)

    try:
        results = await confluence.search_pages(q, config.space_key)
        return {"results": results}
    except Exception as e:
        import structlog
        structlog.get_logger().error("Confluence search failed", error=str(e), query=q)
        raise HTTPException(status_code=500, detail="搜索失败，请稍后重试")


@router.post("/load")
async def load_confluence_page(
    request: ConfluenceLoadRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Load a Confluence page by URL into chat context"""
    # Get user's active config
    config = db.query(ConfluenceConfig).filter(
        ConfluenceConfig.user_id == current_user.id,
        ConfluenceConfig.is_active == True
    ).first()

    if not config:
        raise HTTPException(status_code=400, detail="No Confluence configuration found")

    # Extract page ID from URL
    match = re.search(r'pageId=(\d+)', request.url)
    if not match:
        match = re.search(r'/pages/(\d+)', request.url)
    if not match:
        raise HTTPException(status_code=400, detail="Invalid Confluence URL")

    page_id_str = match.group(1)

    api_token = ConfluenceService.decrypt_token(config.api_token_encrypted)
    confluence = ConfluenceService(config.base_url, config.email, api_token)

    try:
        page_data = await confluence.get_page(page_id_str)
        html_content = page_data["body"]["storage"]["value"]
        markdown_content = confluence.html_to_markdown(html_content)

        # Store or update page in database
        page = db.query(ConfluencePage).filter(
            ConfluencePage.config_id == config.id,
            ConfluencePage.page_id == page_id_str
        ).first()

        if page:
            page.title = page_data["title"]
            page.content_markdown = markdown_content
            page.last_synced_at = datetime.utcnow()
        else:
            page = ConfluencePage(
                config_id=config.id,
                page_id=page_id_str,
                title=page_data["title"],
                space_key=page_data.get("space", {}).get("key", ""),
                content_markdown=markdown_content,
                last_synced_at=datetime.utcnow()
            )
            db.add(page)

        db.commit()
        db.refresh(page)

        return {
            "page": {
                "id": page.id,
                "pageId": page.page_id,
                "title": page.title,
                "spaceKey": page.space_key,
                "contentMarkdown": page.content_markdown
            }
        }
    except Exception as e:
        import structlog
        structlog.get_logger().error("Confluence load failed", error=str(e), url=request.url)
        raise HTTPException(status_code=500, detail="加载页面失败，请检查 URL 是否正确")


@router.post("/test")
async def test_confluence_connection(
    request: ConfluenceTestRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Test Confluence connection with provided credentials"""
    try:
        api_token = request.api_token
        # 如果没有提供 api_token 但有 config_id，使用已保存的 token
        if not api_token and request.config_id:
            config = db.query(ConfluenceConfig).filter(
                ConfluenceConfig.id == request.config_id,
                ConfluenceConfig.user_id == current_user.id
            ).first()
            if config:
                api_token = ConfluenceService.decrypt_token(config.api_token_encrypted)

        if not api_token:
            raise HTTPException(status_code=400, detail="请提供 API Token")

        confluence = ConfluenceService(request.base_url, request.email, api_token)
        # Try to get current user info
        await confluence.get_current_user()
        return {"success": True}
    except HTTPException:
        raise
    except Exception as e:
        import structlog
        structlog.get_logger().error("Confluence test failed", error=str(e))
        raise HTTPException(status_code=400, detail="连接失败，请检查配置信息")


@router.put("/configs/{config_id}")
async def update_config(
    config_id: int,
    config_update: ConfluenceConfigCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update Confluence configuration"""
    config = db.query(ConfluenceConfig).filter(
        ConfluenceConfig.id == config_id,
        ConfluenceConfig.user_id == current_user.id
    ).first()

    if not config:
        raise HTTPException(status_code=404, detail="Configuration not found")

    config.base_url = config_update.base_url
    config.email = config_update.email
    config.space_key = config_update.space_key

    # Only update token if provided
    if config_update.api_token:
        config.api_token_encrypted = ConfluenceService.encrypt_token(config_update.api_token)

    db.commit()
    db.refresh(config)

    return config


@router.post("/writeback/{page_id}")
async def writeback_to_confluence(
    page_id: int,
    request: WriteBackRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Write content back to an existing Confluence page"""
    page = db.query(ConfluencePage).join(ConfluenceConfig).filter(
        ConfluencePage.id == page_id,
        ConfluenceConfig.user_id == current_user.id
    ).first()

    if not page:
        raise HTTPException(status_code=404, detail="Page not found")

    config = page.config
    api_token = ConfluenceService.decrypt_token(config.api_token_encrypted)
    confluence = ConfluenceService(config.base_url, config.email, api_token)

    try:
        # Get current version
        current_page = await confluence.get_page(page.page_id)
        version = current_page["version"]["number"]

        # Convert markdown to HTML
        html_content = confluence.markdown_to_html(request.content)

        # Update page
        title = request.title or page.title
        await confluence.update_page(page.page_id, title, html_content, version)

        # Update local record
        page.title = title
        page.content_markdown = request.content
        page.last_synced_at = datetime.utcnow()
        db.commit()

        return {"success": True, "page_id": page.id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/writeback/new")
async def create_new_confluence_page(
    request: WriteBackRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new Confluence page"""
    if not request.title:
        raise HTTPException(status_code=400, detail="Title is required for new pages")

    config = db.query(ConfluenceConfig).filter(
        ConfluenceConfig.user_id == current_user.id,
        ConfluenceConfig.is_active == True
    ).first()

    if not config:
        raise HTTPException(status_code=400, detail="No Confluence configuration found")

    api_token = ConfluenceService.decrypt_token(config.api_token_encrypted)
    confluence = ConfluenceService(config.base_url, config.email, api_token)

    try:
        html_content = confluence.markdown_to_html(request.content)
        space_key = request.space_key or config.space_key

        if not space_key:
            raise HTTPException(status_code=400, detail="Space key is required")

        result = await confluence.create_page(
            space_key,
            request.title,
            html_content,
            request.parent_id
        )

        # Store in database
        page = ConfluencePage(
            config_id=config.id,
            page_id=result["id"],
            title=result["title"],
            space_key=space_key,
            content_markdown=request.content,
            last_synced_at=datetime.utcnow()
        )
        db.add(page)
        db.commit()
        db.refresh(page)

        return {"success": True, "page_id": page.id, "confluence_page_id": result["id"]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
