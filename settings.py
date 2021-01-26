import os
from dotenv import load_dotenv, find_dotenv


load_dotenv(find_dotenv())


class Settings:
  ASSETS_FOLDER   = os.getenv('ASSETS_FOLDER')
  DATA_PATH       = os.getenv('DATA_PATH')
  FFMPEG_PATH     = os.getenv('FFMPEG_PATH')
  MODEL_NAME      = os.getenv('MODEL_NAME')
  OUTPUT_FILENAME = os.getenv('OUTPUT_FILENAME') or './out/out.mp4'
