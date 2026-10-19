"""Structured outputs the model must return at each step."""

from pydantic import BaseModel, ConfigDict


class _Strict(BaseModel):
    model_config = ConfigDict(extra="forbid")


class Idea(_Strict):
    title: str
    angle: str
    hook: str
    hook_score: int
    product_category: str


class IdeaList(_Strict):
    ideas: list[Idea]


class Scene(_Strict):
    narration: str
    image_prompt: str


class Script(_Strict):
    title: str
    scenes: list[Scene]

    @property
    def narration(self) -> str:
        return " ".join(s.narration for s in self.scenes)


class Caption(_Strict):
    youtube_title: str
    caption: str
    hashtags: list[str]
    disclosure: str
