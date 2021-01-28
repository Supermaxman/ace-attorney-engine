
from dataclasses import dataclass, field
from typing import List, Dict, Set


@dataclass
class Location:
  name: str
  asset_name: str
  extra_assets: List[str] = field(default_factory=list)


@dataclass
class Character:
  name: str
  emotions: Dict[str, List[str]]
  location: Location
  asset_name: str

  def __str__(self):
    return str(self.name).capitalize()


@dataclass
class SoundEffect:
  type: str
  length: int


@dataclass
class MusicEffect:
  track: str


@dataclass
class CharacterSoundEffect:
  sound_effect: SoundEffect
  character: Character


@dataclass
class CueMusicEffect:
  music_effect: MusicEffect
  length: int = 0


@dataclass
class CharacterBeat:
  text: str
  sfx: List[SoundEffect] = field(default_factory=list)
  color: str = None


@dataclass
class Action:
  length: int
  asset_name: str = None
  shake_effect: bool = False
  sound_effect: SoundEffect = None
  music_effect: MusicEffect = None
  emotion_triggers: Set[str] = field(default_factory=set)


@dataclass
class CharacterCue:
  character: Character
  name: str
  beats: List[CharacterBeat]
  emotion: str
  emotion_class: str
  emotion_class_score: float
  actions: List[Action] = field(default_factory=list)
  music: CueMusicEffect = None
  sfx: List[CharacterSoundEffect] = field(default_factory=list)


@dataclass
class CharacterShot:
  cues: List[CharacterCue]

