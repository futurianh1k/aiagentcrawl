"""
News Scraper Models

뉴스 스크레이퍼에서 사용하는 데이터 모델
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from datetime import datetime

from common.models import BaseModel, Comment


@dataclass
class NewsArticle(BaseModel):
    """뉴스 기사 데이터 모델"""
    url: str
    title: str
    content: str
    comments: List[Comment] = field(default_factory=list)
    published_date: Optional[datetime] = None
    source: Optional[str] = None
    keyword: Optional[str] = None
    extraction_method: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """딕셔너리로 변환"""
        result = {
            "url": self.url,
            "title": self.title,
            "content": self.content[:500] + "..." if len(self.content) > 500 else self.content,
            "comments": [comment.to_dict() for comment in self.comments],
            "source": self.source,
            "keyword": self.keyword,
            "extraction_method": self.extraction_method,
        }
        if self.published_date:
            result["published_date"] = self.published_date.isoformat()
        return result

