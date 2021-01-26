
import os

import engine
from settings import Settings
from comments import Author
from script_constants import Character
import data_utils


if __name__ == '__main__':
  # settings
  os.environ["PATH"] += ';' + Settings.FFMPEG_PATH
  data_path = Settings.DATA_PATH
  max_length = Settings.MAX_COMMENT_LENGTH
  output_filename = Settings.OUTPUT_FILENAME

  characters = [
    Author(
      name='Randolph',
      character=Character.JUDGE
    ),
    Author(
      name='Kaffee',
      character=Character.PHOENIX
    ),
    Author(
      name='Jessep',
      character=Character.GUMSHOE
    ),
    Author(
      name='Ross',
      character=Character.EDGEWORTH
    ),
  ]
  comments = data_utils.load_script(
    data_path,
    characters,
    max_length
  )

  engine = engine.PhoenixEngine(
    theme=Settings.THEME,
    emotion_model=Settings.EMOTION_MODEL,
    sentence_model=Settings.SENTENCE_MODEL,
    emotion_threshold=Settings.EMOTION_THRESHOLD,
    music_min_scene_duration=Settings.MUSIC_MIN_SCENE_DURATION,
    fps=Settings.FPS,
    video_codec=Settings.VIDEO_CODEC,
    audio_codec=Settings.AUDIO_CODEC,
    video_bitrate=Settings.VIDEO_BITRATE,
    lag_frames=Settings.LAG_FRAMES,
    num_processes=Settings.NUM_PROCESSES,
    scaling_factor=Settings.SCALING_FACTOR,
    assets_folder=Settings.ASSETS_FOLDER,
    cache_folder=Settings.CACHE_FOLDER,
  )
  engine.animate(
    comments,
    output_filename
  )
