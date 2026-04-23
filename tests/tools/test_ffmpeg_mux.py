from pedagogica_tools.ffmpeg_mux import build_concat_synced_content


def test_build_concat_synced_content_uses_sorted_scene_relative_paths() -> None:
    assert build_concat_synced_content(["scene_02", "scene_01"]) == (
        "file 'scenes/scene_01/synced.mp4'\n"
        "file 'scenes/scene_02/synced.mp4'\n"
    )
