from celery import shared_task
from crawling_view.genie_crawler_views import GenieSearchSong, GenieSongCrawler, save_each_to_csv, save_to_db
import logging

logger = logging.getLogger(__name__)

# ------------------------------ rhoonart ------------------------------
class rhoonart_songs:
    jaerium = [
        "Beneath the Frozen Sky",
        "The Wisp of Winter",
        "Sparkles of the Night",
        "Soft Breezes in Winter",
        "The New Year’s Moment",
        "Cheers to the Future",
        "Softness in the Snow",
        "The Frost of Dreams"
    ]
    anonatsue = [
        "Dreamy Orchards",
        "Emerald Symphony",
        "Sunbeam Reflections",
        "Warm Breeze Serenade",
        "Velvet Dawn",
        "Enchanted Bloom",
        "Lush Springtime",
        "Cascading Waterfall",
        "Fragrant Twilight",
        "Cherry Blossom Serenade",
        "Soft Petal Waltz",
        "Garden of Serenity",
        "Wind’s Caress",
        "Secret Garden Lullaby",
        "Azure Morning",
        "Lush Green Fields",
        "Meadow Whispers"
    ]

    @staticmethod
    def crawl_artist(artist_name, song_names):
        search_song = GenieSearchSong()
        company_name = "rhoonart" # 회사명
        artist_song_list = [(artist_name, song) for song in song_names] # 아티스트명, 곡명 리스트
        search_results = search_song.search_multiple(artist_song_list) # 검색 결과
        html_list = [item['html'] for item in search_results] # 검색 결과에서 html 추출
        result_list = GenieSongCrawler.crawl(html_list, artist_song_list) # 곡 정보 추출    
        logger.info(f"GenieSongCrawler result: {result_list}")

        save_to_db({info['song_name']: info for info in result_list}) # DB 저장
        logger.info("✅ DB 저장 완료")
        
        filepaths = save_each_to_csv({info['song_name']: info for info in result_list}, company_name, 'youtube_music') # CSV 저장
        logger.info(f"✅ CSV 저장 완료: {filepaths}")
        return result_list

# ------------------------------ Jaerium ------------------------------
@shared_task
def genie_crawl_jaerium_test():
    return rhoonart_songs.crawl_artist("제이리움", rhoonart_songs.jaerium)

# ------------------------------ anonatsue ------------------------------
@shared_task
def genie_crawl_anonatsue_test():
    return rhoonart_songs.crawl_artist("anonatsue", rhoonart_songs.anonatsue)