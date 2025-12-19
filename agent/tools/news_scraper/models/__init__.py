"""
News Scraper Models Package

models.py의 내용을 re-export하여 호환성 유지
models 디렉토리와 models.py 파일이 모두 있어서 충돌 방지
"""

# 상위 디렉토리의 models.py 파일을 직접 import
import importlib.util
import os

# models.py 파일 경로
parent_dir = os.path.dirname(os.path.dirname(__file__))
models_file = os.path.join(parent_dir, "models.py")

# models.py를 모듈로 로드
spec = importlib.util.spec_from_file_location("news_scraper_models", models_file)
news_scraper_models = importlib.util.module_from_spec(spec)
spec.loader.exec_module(news_scraper_models)

# NewsArticle export
NewsArticle = news_scraper_models.NewsArticle

# common.models에서 Comment import
from common.models import Comment

__all__ = ["NewsArticle", "Comment"]
