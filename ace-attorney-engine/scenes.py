
from dataclasses import dataclass, field
from typing import List, Dict

from script_constants import Character, Action, Location, audio_emotions


@dataclass
class SoundEffect:
  type: str
  length: int
  character: str = None


@dataclass
class MusicEffect:
  track: str = audio_emotions['normal']
  length: int = 0


@dataclass
class CharacterBeat:
  text: str
  sfx: List[SoundEffect] = field(default_factory=list)
  color: str = None


@dataclass
class CharacterCue:
  character: Character
  name: str
  beats: List[CharacterBeat]
  location: Location
  emotion: str
  emotion_class: str
  emotion_class_score: float
  actions: List[Action] = field(default_factory=list)
  music: MusicEffect = None
  sfx: List[SoundEffect] = field(default_factory=list)


@dataclass
class CharacterShot:
  cues: List[CharacterCue]

