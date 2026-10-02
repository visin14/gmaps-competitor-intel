import os, json, textwrap, hashlib
from PIL import Image, ImageDraw, ImageFont

PALETTES = [((142, 68, 173), (233, 150, 200)), ((41, 128, 185), (109, 213, 250)), ((211, 84, 0), (247, 202, 24)),
            ((22, 160, 133), (171, 235, 198)), ((192, 57, 43), (250, 160, 160))]


def _font(size):
    for name in ('arial.ttf', 'DejaVuSans.ttf', 'Arial.ttf'):
        try:
            return ImageFont.truetype(name, size)
        except OSError:
            continue
    return ImageFont.load_default()


def make_demo_image(app, project_id, competitor_id, competitor_name, topic, seed_key) -> str:
    """Create a simple illustrative card for demo posts. Returns the web path (static/media/...)."""
    media_folder = app.config['MEDIA_FOLDER'].replace('\\', '/')
    folder = os.path.join(app.root_path, media_folder, str(project_id), str(competitor_id))
    name = f'demo_{hashlib.md5(seed_key.encode()).hexdigest()[:8]}.jpg'
    path = os.path.join(folder, name)
    web_path = f'{media_folder}/{project_id}/{competitor_id}/{name}'
    if os.path.exists(path):
        return web_path
    try:
        os.makedirs(folder, exist_ok=True)
        top, bottom = PALETTES[int(hashlib.md5(topic.encode()).hexdigest(), 16) % len(PALETTES)]
        w, h = 640, 400
        img = Image.new('RGB', (w, h))
        px = img.load()
        for y in range(h):
            t = y / h
            row = tuple(int(top[i] * (1 - t) + bottom[i] * t) for i in range(3))
            for x in range(w):
                px[x, y] = row
        d = ImageDraw.Draw(img)
        d.text((36, 40), competitor_name, font=_font(30), fill='white')
        y = 150
        for line in textwrap.wrap(topic, 22):
            d.text((36, y), line, font=_font(46), fill='white')
            y += 58
        d.text((36, h - 48), 'demo image', font=_font(18), fill=(255, 255, 255))
        img.save(path, 'JPEG', quality=85)
    except OSError:
        pass  # read-only filesystem: the image is expected to ship with the deployment
    return web_path


SAMPLE_IDEAS = [
    ('Monsoon Frizz Rescue Week', '🌧️ Monsoon humidity ruining your blow-dry? Our Frizz Rescue Week pairs a deep-conditioning spa with an anti-frizz finish at a special price. Our stylists will recommend the right routine for your hair type. Slots are limited, so book early!',
     ['monsoon hair care', 'anti frizz', 'hair spa'], 'Book your Frizz Rescue slot', 'Glossy, frizz-free hair with raindrops on a window behind'),
    ('Student Glow-Up Days', '🎓 Back to college? Walk in with your student ID and enjoy a fresh cut and style at a friendly price. Our team keeps trends affordable without compromising on quality. Bring a friend and we will make it a fun afternoon!',
     ['student discount', 'haircut offer', 'college'], 'Show your student ID at the front desk', 'Two students with fresh hairstyles laughing together'),
    ('Pre-Bridal Planning Consultations', '👰 Planning a wedding? Book a free pre-bridal consultation and we will map out your hair, skin and makeup timeline month by month. Trials can be scheduled around your calendar. Start early and glow on the big day!',
     ['bridal makeup', 'pre bridal', 'wedding salon'], 'Reserve a free consultation', 'Bride mid-trial with soft natural light and a mood board'),
    ('Sunday Head-Massage Treat', '☀️ Sundays are for self-care! Enjoy a complimentary 10-minute head massage with any service above ₹500 between 10 AM and 2 PM. No appointment needed, just walk in and relax. See you this weekend!',
     ['sunday offer', 'head massage', 'walk in salon'], 'Walk in this Sunday', 'Relaxed client enjoying a head massage in a bright salon'),
    ('Meet Our Colour Specialists', '🎨 Meet the colour team behind our most-loved transformations! With years of experience in balayage, global colour and fashion shades, they will guide you to the look that suits you. Book a colour consultation this week.',
     ['hair colour', 'balayage', 'colour specialist'], 'Book a colour consultation', 'Colourist holding up swatches next to a smiling client'),
]
