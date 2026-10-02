import os, re, io, json, hashlib, logging
import requests
from PIL import Image


def enlarge_google_image(url: str, width: int = 800) -> str:
    """Google image URLs end in size params like '=w86-h86-k-no'; ask for a bigger rendition."""
    return re.sub(r'=[swh]\d+[^/?#]*$', f'=w{width}', url)


def download_image(url: str, project_id: int, competitor_id: int, filename_prefix: str,
                   media_root: str = None, web_prefix: str = 'static/media'):
    """Download an image into <media_root>/<project>/<competitor>/ and return its web path
    (e.g. 'static/media/1/3/p1_ab12cd34.jpg'), or None on failure."""
    if not url or not url.startswith('http'):
        return None
    media_root = media_root or os.path.join('static', 'media')
    try:
        folder = os.path.join(media_root, str(project_id), str(competitor_id))
        os.makedirs(folder, exist_ok=True)

        response = requests.get(enlarge_google_image(url), timeout=10, headers={'User-Agent': 'Mozilla/5.0'})
        response.raise_for_status()
        if len(response.content) > 3 * 1024 * 1024:
            return None

        img = Image.open(io.BytesIO(response.content))
        img.load()
        if img.mode not in ('RGB', 'L'):
            img = img.convert('RGB')

        filename = f'{filename_prefix}_{hashlib.md5(url.encode()).hexdigest()[:8]}.jpg'
        img.save(os.path.join(folder, filename), 'JPEG', quality=88)

        return f'{web_prefix.strip("/")}/{project_id}/{competitor_id}/{filename}'
    except Exception as e:
        logging.error('Image download failed (%s): %s', url[:80], e)
        return None


def get_images_for_api(image_paths_json: str) -> list:
    try:
        paths = json.loads(image_paths_json)
        result = []
        for path in paths:
            if isinstance(path, dict) and 'url' in path:
                result.append(path)
            elif isinstance(path, str):
                result.append({'url': '/' + path})
        return result
    except Exception:
        return []
