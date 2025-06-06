import logging
from crawling_view.youtube_crawler_views import YouTubeSongCrawler

# 로깅 기본 설정
logging.basicConfig(
    level=logging.INFO,  # 기본 로그 레벨 (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    format='[%(levelname)s] %(asctime)s - %(name)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

if __name__ == "__main__":
    logging.info("크롤링 시작")
    YouTubeSongCrawler.delay()