
import os
from dotenv import load_dotenv, find_dotenv


load_dotenv(find_dotenv())


class Settings:
  ASSETS_FOLDER             = os.getenv('ASSETS_FOLDER')
  DATA_PATH                 = os.getenv('DATA_PATH')
  FFMPEG_PATH               = os.getenv('FFMPEG_PATH')
  OUTPUT_FILENAME           = os.getenv('OUTPUT_FILENAME') or '../out/out.mp4'
  CACHE_FOLDER              = os.getenv('CACHE_FOLDER') or '../cache'
  EMOTION_MODEL             = os.getenv('EMOTION_MODEL') or 'mrm8488/t5-base-finetuned-emotion'
  SENTENCE_MODEL            = os.getenv('SENTENCE_MODEL') or 'en_core_web_sm'
  EMOTION_THRESHOLD         = float(os.getenv('EMOTION_THRESHOLD') or 0.5)
  MAX_COMMENT_LENGTH        = int(os.getenv('MAX_COMMENT_LENGTH') or 100_000)
  MUSIC_MIN_SCENE_DURATION  = int(os.getenv('MUSIC_MIN_SCENE_DURATION') or 4)
  THEME                     = os.getenv('THEME') or 'classic'
  FPS                       = int(os.getenv('FPS') or 18)
  VIDEO_CODEC               = os.getenv('VIDEO_CODEC') or 'libx264'
  AUDIO_CODEC               = os.getenv('AUDIO_CODEC') or 'aac'
  VIDEO_CRF                 = int(os.getenv('VIDEO_CRF') or 19)
  LAG_FRAMES                = int(os.getenv('LAG_FRAMES') or 25)
  DEFAULT_ANIMATION_LENGTH  = int(os.getenv('DEFAULT_ANIMATION_LENGTH') or 11)
  SCALING_FACTOR            = float(os.getenv('SCALING_FACTOR') or 2.0)
