import os
from typing import Optional, List
from pexels_api import API


class ImageSearcher:
    def __init__(self):
        api_key = os.getenv("PEXELS_API_KEY")
        if not api_key:
            raise ValueError("PEXELS_API_KEY not configured")
        self.client = API(api_key)

    def search_fashion_image(self, keywords: List[str]) -> Optional[str]:
        """搜索时尚穿搭图片，返回 portrait 方向的图片 URL"""
        query = " ".join(keywords)
        self.client.search(query, results_per_page=10)
        photos = self.client.get_entries()

        for photo in photos:
            if photo.portrait:
                return photo.portrait

        if photos:
            return photos[0].large

        return None


image_searcher = ImageSearcher()
