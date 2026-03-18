from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from .models import ImageLayer, LayerType, ProjectModel, TextAlignment, TextLayer
from .text_utils import TextProcessor


class PreviewRenderError(RuntimeError):
    pass


def _load_font(layer: TextLayer) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    if layer.font_path and Path(layer.font_path).exists():
        try:
            return ImageFont.truetype(layer.font_path, layer.font_size)
        except OSError:
            pass
    return ImageFont.load_default()


def _render_image_layer(result: Image.Image, layer: ImageLayer):
    if not layer.visible or not layer.image_path:
        return

    image_path = Path(layer.image_path)
    if not image_path.exists():
        return

    overlay = Image.open(image_path).convert("RGBA")
    overlay = overlay.resize((layer.size.width, layer.size.height))

    if layer.opacity < 1.0:
        alpha = overlay.getchannel("A")
        alpha = alpha.point(lambda value: int(value * layer.opacity))
        overlay.putalpha(alpha)

    if layer.rotation:
        overlay = overlay.rotate(layer.rotation, expand=True)

    result.paste(overlay, (layer.position.x, layer.position.y), overlay)


def _draw_text_layer(draw: ImageDraw.ImageDraw, layer: TextLayer):
    if not layer.visible:
        return

    font = _load_font(layer)
    text = TextProcessor.process_text(
        layer.text,
        font,
        layer.max_width,
        layer.truncate_suffix,
    )
    if not text:
        return

    text_width, text_height = TextProcessor.get_text_size(text, font)
    anchor_x = layer.position.x
    anchor_y = layer.position.y

    if layer.horizontal_align == TextAlignment.CENTER:
        draw_x = anchor_x - text_width // 2
    elif layer.horizontal_align == TextAlignment.RIGHT:
        draw_x = anchor_x - text_width
    else:
        draw_x = anchor_x

    if layer.vertical_align == TextAlignment.MIDDLE:
        draw_y = anchor_y - text_height // 2
    elif layer.vertical_align == TextAlignment.BOTTOM:
        draw_y = anchor_y - text_height
    else:
        draw_y = anchor_y

    draw.text((draw_x, draw_y), text, font=font, fill=layer.color)


def render_project_image(project_model: ProjectModel) -> Image.Image:
    base_image = project_model.base_image
    if not base_image or not base_image.image_path:
        raise PreviewRenderError("请先设置底图后再进行预览。")

    base_image_path = Path(base_image.image_path)
    if not base_image_path.exists():
        raise PreviewRenderError(f"底图不存在: {base_image.image_path}")

    result = Image.open(base_image_path).convert("RGBA")

    for layer in project_model.get_layers_by_type(LayerType.IMAGE):
        if isinstance(layer, ImageLayer):
            _render_image_layer(result, layer)

    draw = ImageDraw.Draw(result)
    for layer in project_model.get_layers_by_type(LayerType.TEXT):
        if isinstance(layer, TextLayer):
            _draw_text_layer(draw, layer)

    return result
