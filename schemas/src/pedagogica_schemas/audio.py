from pydantic import BaseModel

from pedagogica_schemas.base import BaseMessage


class WordTiming(BaseModel):
    word: str
    start_seconds: float
    end_seconds: float
    char_start: int
    char_end: int


class AudioClip(BaseMessage):
    schema_version: str = "0.1.0"
    scene_id: str
    audio_path: str
    total_duration_seconds: float
    word_timings: list[WordTiming]
    voice_id: str
    model_id: str
    char_count: int
