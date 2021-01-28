
import os

import engine
from settings import Settings
from comments import Author
from game_themes import ClassicTheme

import data_utils


if __name__ == '__main__':
  # settings
  os.environ["PATH"] += ';' + Settings.FFMPEG_PATH
  data_path = Settings.DATA_PATH
  max_length = Settings.MAX_COMMENT_LENGTH
  output_filename = Settings.OUTPUT_FILENAME

  theme = ClassicTheme(
    Settings.ASSETS_FOLDER,
    Settings.SCALING_FACTOR
  )

  characters = [
    Author(
      name='Randolph',
      character=theme.Character.JUDGE
    ),
    Author(
      name='Kaffee',
      character=theme.Character.PHOENIX
    ),
    Author(
      name='Jessep',
      character=theme.Character.GUMSHOE
    ),
    Author(
      name='Ross',
      character=theme.Character.EDGEWORTH
    ),
  ]
  comments = data_utils.load_script(
    data_path,
    characters,
    max_length
  )
  engine = engine.PhoenixEngine(
    theme=theme,
    emotion_model=Settings.EMOTION_MODEL,
    sentence_model=Settings.SENTENCE_MODEL,
    emotion_threshold=Settings.EMOTION_THRESHOLD,
    music_min_scene_duration=Settings.MUSIC_MIN_SCENE_DURATION,
    fps=Settings.FPS,
    video_codec=Settings.VIDEO_CODEC,
    audio_codec=Settings.AUDIO_CODEC,
    video_crf=Settings.VIDEO_CRF,
    lag_frames=Settings.LAG_FRAMES,
    default_animation_length=Settings.DEFAULT_ANIMATION_LENGTH,
    cache_folder=Settings.CACHE_FOLDER,
  )
  engine.animate(
    comments,
    output_filename
  )
