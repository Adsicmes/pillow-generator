from pathlib import Path

from PIL import Image

from src.core.models import ImageLayer, Position, ProjectModel, Size, TextLayer
from src.core.renderer import render_project_image


def create_png(path: Path, color: tuple[int, int, int, int], size: tuple[int, int]):
    Image.new("RGBA", size, color).save(path)


def test_render_project_image_composes_layers(tmp_path: Path):
    base_image_path = tmp_path / "base.png"
    overlay_path = tmp_path / "overlay.png"
    create_png(base_image_path, (255, 255, 255, 255), (120, 80))
    create_png(overlay_path, (255, 0, 0, 255), (20, 20))

    project = ProjectModel()
    project.set_base_image(str(base_image_path), "底图")
    project.add_layer(
        ImageLayer(
            name="角标",
            image_path=str(overlay_path),
            size=Size(20, 20),
            position=Position(10, 15),
        )
    )
    project.add_layer(
        TextLayer(
            name="标题",
            text="Hello",
            position=Position(60, 40),
        )
    )

    result = render_project_image(project)

    assert result.size == (120, 80)
    assert result.tobytes() != Image.open(base_image_path).tobytes()
