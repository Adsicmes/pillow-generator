from pathlib import Path

from PIL import Image

from src.core.models import ImageLayer, ProjectModel, Size
from src.core.project_manager import ProjectManager


def create_png(path: Path, color: tuple[int, int, int, int]):
    Image.new("RGBA", (32, 32), color).save(path)


def test_project_manager_tracks_unsaved_changes():
    manager = ProjectManager()
    project = ProjectModel()

    manager.reset_tracking(project)
    assert not manager.is_project_modified(project)

    project.function_name = "generate_card"
    assert manager.is_project_modified(project)


def test_project_manager_resets_dirty_state_after_save_and_load(tmp_path: Path):
    manager = ProjectManager()
    project = ProjectModel()

    base_image_path = tmp_path / "base.png"
    overlay_path = tmp_path / "overlay.png"
    create_png(base_image_path, (20, 30, 40, 255))
    create_png(overlay_path, (200, 50, 50, 180))

    project.set_base_image(str(base_image_path), "底图")
    project.add_layer(
        ImageLayer(
            name="图片层",
            image_path=str(overlay_path),
            size=Size(24, 24),
        )
    )

    project_file = tmp_path / "sample.pgp"
    assert manager.save_project(project, str(project_file))
    assert not manager.is_project_modified(project)

    project.function_name = "generate_other"
    assert manager.is_project_modified(project)

    loaded_project = ProjectModel()
    assert manager.load_project(loaded_project, str(project_file))
    assert not manager.is_project_modified(loaded_project)
