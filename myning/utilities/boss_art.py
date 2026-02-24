from functools import lru_cache

from chafa import Canvas, CanvasConfig, PixelType
from PIL import Image
from rich.text import Text

from myning.objects.mine import BossConfig


@lru_cache(maxsize=16)
def render_boss_art(boss_config: BossConfig) -> Text:
    config = CanvasConfig()
    image = Image.open(f"./{boss_config.image}").convert("RGB")
    config.width = 80
    config.height = 35
    config.calc_canvas_geometry(image.width, image.height, 11 / 24)
    bands = len(image.getbands())
    pixels = image.tobytes()
    canvas = Canvas(config)
    canvas.draw_all_pixels(
        PixelType.CHAFA_PIXEL_RGB8,
        pixels,  # type: ignore
        image.width,
        image.height,
        image.width * bands,
    )
    output = canvas.print()
    return Text.from_ansi(output.decode())
