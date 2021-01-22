
import cv2
from typing import List, Dict
import os
from pydub import AudioSegment
import ffmpeg
import random
from textwrap import wrap
import spacy
from tqdm import tqdm
import string
from multiprocessing import Pool

from script_constants import Location, Character, Action, location_map, character_map, character_location_map, \
  audio_emotions, character_emotions, objection_emotions, shake_emotions, hold_it_emotions

from animation import anim_cache, AnimScene, AnimVideo


def split_str_into_newlines(text: str, max_line_count: int = 34):
  words = text.split(" ")
  new_text = ""
  for word in words:
    last_sentence = new_text.split("\n")[-1] + word + " "
    if len(last_sentence) >= max_line_count:
      new_text += "\n" + word + " "
    else:
      new_text += word + " "
  return new_text


def process_scene(args):
  scene_id, scene, assets_folder, default_length, lag_frames = args
  sound_effects = []
  scenes = []
  bg = anim_cache.get_anim_img(f'{assets_folder}/{location_map[scene["location"]]}')
  arrow = anim_cache.get_anim_img(f"{assets_folder}/arrow.png", x=235, y=170, w=15, h=15, key_x=5)
  textbox = anim_cache.get_anim_img(f"{assets_folder}/textbox4.png", w=bg.w)

  bench = None
  if scene["location"] == Location.COURTROOM_LEFT:
    bench = anim_cache.get_anim_img(f"{assets_folder}/logo-left.png")
  elif scene["location"] == Location.COURTROOM_RIGHT:
    bench = anim_cache.get_anim_img(f"{assets_folder}/logo-right.png")
  elif scene["location"] == Location.WITNESS_STAND:
    bench = anim_cache.get_anim_img(f"{assets_folder}/witness_stand.png", w=bg.w)
    bench.y = bg.h - bench.h
  if "audio" in scene:
    sound_effects.append({"_type": "bg", "src": f'{assets_folder}/{scene["audio"]}.mp3'})
  current_frame = 0
  current_character_name = None
  text = None
  for obj in scene["scene"]:
    if "character" in obj:
      _dir = f'{assets_folder}/{character_map[obj["character"]]}'
      current_character_name = str(obj["character"])
      character_name = anim_cache.get_anim_text(
        current_character_name,
        font_path=f"{assets_folder}/igiari/Igiari.ttf",
        font_size=12,
        x=4,
        y=113,
      )
      default = "normal" if "emotion" not in obj else obj["emotion"]
      default_path = (
        f"{_dir}/{current_character_name.lower()}-{default}(a).gif"
      )
      if not os.path.isfile(default_path):
        default_path = (
          f"{_dir}/{current_character_name.lower()}-{default}.gif"
        )
      default_character = anim_cache.get_anim_img(default_path, half_speed=True)
      if "(a)" in default_path:
        talking_character = anim_cache.get_anim_img(
          default_path.replace("(a)", "(b)"), half_speed=True
        )
      else:
        talking_character = anim_cache.get_anim_img(default_path, half_speed=True)
    if "emotion" in obj:
      default = obj["emotion"]
      default_path = (
        f"{_dir}/{current_character_name.lower()}-{default}(a).gif"
      )
      if not os.path.isfile(default_path):
        default_path = (
          f"{_dir}/{current_character_name.lower()}-{default}.gif"
        )
      default_character = anim_cache.get_anim_img(default_path, half_speed=True)
      if "(a)" in default_path:
        talking_character = anim_cache.get_anim_img(
          default_path.replace("(a)", "(b)"), half_speed=True
        )
      else:
        talking_character = anim_cache.get_anim_img(default_path, half_speed=True)
    if "action" in obj and (
        obj["action"] == Action.TEXT
        or obj["action"] == Action.TEXT_SHAKE_EFFECT
    ):
      # TODO speed this up, too slow
      character = talking_character
      _text = split_str_into_newlines(obj["text"])
      _colour = None if "colour" not in obj else obj["colour"]
      text = anim_cache.get_anim_text(
        _text,
        font_path=f"{assets_folder}/igiari/Igiari.ttf",
        font_size=15,
        x=5,
        y=130,
        typewriter_effect=True,
        colour=_colour,
      )
      num_frames = len(_text) + lag_frames
      _character_name = character_name
      if "name" in obj:
        _character_name = anim_cache.get_anim_text(
          obj["name"],
          font_path=f"{assets_folder}/igiari/Igiari.ttf",
          font_size=12,
          x=4,
          y=113,
        )
      if obj["action"] == Action.TEXT_SHAKE_EFFECT:
        bg.shake_effect = True
        character.shake_effect = True
        if bench is not None:
          bench.shake_effect = True
        textbox.shake_effect = True
      scenes.append(
        AnimScene([bg, character, bench, textbox, _character_name, text], len(_text) - 1, start_frame=current_frame)
      )
      sound_effects.append({"_type": "bip", "length": len(_text) - 1})
      if obj["action"] == Action.TEXT_SHAKE_EFFECT:
        bg.shake_effect = False
        character.shake_effect = False
        if bench is not None:
          bench.shake_effect = False
        textbox.shake_effect = False
      text.typewriter_effect = False
      character = default_character
      scenes.append(
        AnimScene([bg, character, bench, textbox, _character_name, text, arrow], lag_frames, start_frame=len(_text) - 1)
      )
      current_frame += num_frames
      sound_effects.append({"_type": "silence", "length": lag_frames})

    elif "action" in obj and obj["action"] == Action.SHAKE_EFFECT:
      character = default_character
      bg.shake_effect = True
      character.shake_effect = True
      if bench is not None:
        bench.shake_effect = True
      textbox.shake_effect = True

      if text is not None:
        scene_objs = [
          bg,
          character,
          bench,
          textbox,
          character_name,
          text,
          arrow,
        ]
      else:
        scene_objs = [bg, character, bench]
      scenes.append(
        AnimScene(scene_objs, lag_frames, start_frame=current_frame)
      )
      sound_effects.append({"_type": "shock", "length": lag_frames})
      current_frame += lag_frames
      bg.shake_effect = False
      character.shake_effect = False
      if bench is not None:
        bench.shake_effect = False
      textbox.shake_effect = False
    elif "action" in obj and obj["action"] == Action.OBJECTION:
      effect_image = anim_cache.get_anim_img(f"{assets_folder}/objection.gif", shake_effect=True)
      character = default_character
      scenes.append(AnimScene([bg, character, bench, effect_image], default_length, start_frame=current_frame))
      scenes.append(AnimScene([bg, character, bench], default_length, start_frame=current_frame))

      sound_effects.append(
        {
          "_type": "objection",
          "character": current_character_name.lower(),
          "length": 2 * default_length,
        }
      )
      current_frame += default_length
    elif "action" in obj and obj["action"] == Action.HOLD_IT:
      effect_image = anim_cache.get_anim_img(f"{assets_folder}/holdit.gif", shake_effect=True)
      character = default_character
      scenes.append(AnimScene([bg, character, bench, effect_image], default_length, start_frame=current_frame))
      scenes.append(AnimScene([bg, character, bench], default_length, start_frame=current_frame))
      sound_effects.append(
        {
          "_type": "objection",
          "character": current_character_name.lower(),
          "length": 2 * default_length,
        }
      )
      current_frame += default_length
    else:
      character = default_character
      _length = lag_frames
      if "length" in obj:
        _length = obj["length"]
      if "repeat" in obj:
        character.repeat = obj["repeat"]
      scenes.append(AnimScene([bg, character, bench], _length, start_frame=current_frame))
      character.repeat = True
      sound_effects.append({"_type": "silence", "length": _length})
      current_frame += _length
  return scene_id, scenes, sound_effects


def do_video(
    config: List[Dict], assets_folder, fps, lag_frames=25,
    cache_video_codec=None, cache_video_extension='avi', cache_folder='cache'
):
  default_length = 11
  scene_jobs = [(scene_id, scene, assets_folder, default_length, lag_frames) for scene_id, scene in enumerate(config)]
  results = []
  with Pool(processes=10) as p:
    for scene_id, scene_animations, scene_sfx in tqdm(
        p.imap_unordered(process_scene, scene_jobs), total=len(scene_jobs), desc='creating video...'
    ):
      results.append((scene_id, scene_animations, scene_sfx))

  scenes = []
  sound_effects = []
  for scene_id, scene_animations, scene_sfx in sorted(results, key=lambda x: x[0]):
    scenes.extend(scene_animations)
    sound_effects.extend(scene_sfx)

  video = AnimVideo(scenes, fps=fps, extension=cache_video_extension, codec=cache_video_codec)
  video.render(f"{cache_folder}/video.{cache_video_extension}")
  return sound_effects


def do_audio(sound_effects: List[Dict], assets_folder, fps, cache_folder='cache'):
  audio_se = AudioSegment.empty()
  bip = AudioSegment.from_wav(
    f"{assets_folder}/sfx general/sfx-blipmale.wav"
  ) + AudioSegment.silent(duration=50)
  blink = AudioSegment.from_wav(f"{assets_folder}/sfx general/sfx-blink.wav")
  blink -= 10
  badum = AudioSegment.from_wav(f"{assets_folder}/sfx general/sfx-fwashing.wav")
  long_bip = bip * 100
  long_bip -= 10
  spf = 1 / fps * 1000
  pheonix_objection = AudioSegment.from_mp3(f"{assets_folder}/Phoenix - objection.mp3")
  edgeworth_objection = AudioSegment.from_mp3(
    f"{assets_folder}/Edgeworth - (English) objection.mp3"
  )
  default_objection = AudioSegment.from_mp3(f"{assets_folder}/Payne - Objection.mp3")

  # loop through all sfx which are not music tracks and combine them into a single track
  for obj in tqdm(sound_effects, total=len(sound_effects), desc='creating sound effects...'):
    obj_type = obj["_type"]
    obj_length = 0
    if 'length' in obj:
      obj_length = obj["length"]
    obj_duration = int(obj_length * spf)
    if obj_type == "silence":
      audio_se += AudioSegment.silent(duration=obj_duration)
    elif obj_type == "bip":
      obj_duration -= len(blink)
      audio_se += blink + long_bip[:obj_duration]
    elif obj_type == "objection":
      obj_character = obj["character"]
      if obj_character == "phoenix":
        audio_se += pheonix_objection[:obj_duration]
      elif obj_character == "edgeworth":
        audio_se += edgeworth_objection[:obj_duration]
      else:
        audio_se += default_objection[:obj_duration]
    elif obj_type == "shock":
      audio_se += badum[:obj_duration]

  music_tracks = []
  len_counter = 0
  # loop through all music tracks and determine their length based on sound effects between them
  for obj in sound_effects:
    if obj["_type"] == "bg":
      if len(music_tracks) > 0:
        music_tracks[-1]["length"] = len_counter
        len_counter = 0
      music_tracks.append({"src": obj["src"]})
    else:
      len_counter += obj["length"]
  if len(music_tracks) > 0 and len_counter > 0:
    music_tracks[-1]["length"] = len_counter

  music_se = AudioSegment.empty()
  # create music track based on computed lengths and combine tracks together
  for track in tqdm(music_tracks, total=len(music_tracks), desc='creating music...'):
    track_length = track["length"]
    track_duration = int(track_length * spf)
    music_se += AudioSegment.from_mp3(track["src"])[:track_duration]

  final_se = audio_se.overlay(music_se)
  final_se.export(f"{cache_folder}/audio.mp3", format="mp3")


def ace_attorney_animate(
    config: List[Dict],
    output_filename: str = f"output.mp4",
    assets_folder='assets',
    fps=18,
    video_codec='libx264',
    audio_codec='aac',
    cache_video_codec=cv2.VideoWriter_fourcc(*'MPEG'),
    cache_video_extension='avi',
    cache_folder='cache'
):
  if not os.path.exists(cache_folder):
    os.mkdir(cache_folder)

  sound_effects = do_video(
    config, assets_folder, fps,
    cache_video_codec=cache_video_codec,
    cache_video_extension=cache_video_extension,
    cache_folder=cache_folder,
  )
  do_audio(sound_effects, assets_folder, fps)
  video = ffmpeg.input(f"{cache_folder}/video.{cache_video_extension}")
  audio = ffmpeg.input(f"{cache_folder}/audio.mp3")
  if os.path.exists(output_filename):
    os.remove(output_filename)
  out = ffmpeg.output(
    video,
    audio,
    output_filename,
    vcodec=video_codec,
    acodec=audio_codec,
    strict="experimental",
  )
  out.run(capture_stdout=True, capture_stderr=True)


def get_characters(most_common: List):
  characters = {Character.PHOENIX: most_common[0]}
  if len(most_common) > 0:
    characters[Character.EDGEWORTH] = most_common[1]
    if len(most_common) > 1:
      for character in most_common[2:]:
        rnd_characters = [
          Character.GODOT,
          Character.FRANZISKA,
          Character.JUDGE,
          Character.LARRY,
          Character.MAYA,
          Character.KARMA,
          Character.PAYNE,
          Character.MAGGEY,
          Character.PEARL,
          Character.LOTTA,
          Character.GUMSHOE,
          Character.GROSSBERG,
        ]
        rnd_character = random.choice(
          list(
            filter(
              lambda character: character not in characters, rnd_characters
            )
          )
        )
        characters[rnd_character] = character
  return characters


def comments_to_scene(comments: List, emotion_threshold=0.5, **kwargs):
  nlp = spacy.load("en_core_web_sm")
  audio_min_scene_duration = 4
  scene = []
  for comment in comments:
    tokens = nlp(comment.body)
    sentences = [sent.string.strip() for sent in tokens.sents]
    joined_sentences, current_sentence = [], None
    for sentence in sentences:
      if len(sentence) > 90:
        text_chunks = []
        text_wrap = wrap(sentence, 85)
        for idx, chunk in enumerate(text_wrap):
          if chunk[-1] in string.punctuation:
            chunk_text = chunk
          else:
            if idx != len(text_wrap) - 1:
              chunk_text = f"{chunk}..."
            else:
              chunk_text = chunk
          text_chunks.append(chunk_text)
        joined_sentences.extend(text_chunks)
        current_sentence = None
      else:
        if current_sentence is not None and len(current_sentence) + len(sentence) + 1 <= 90:
          current_sentence += " " + sentence
        else:
          if current_sentence is not None:
            joined_sentences.append(current_sentence)
          current_sentence = sentence
    if current_sentence is not None:
      joined_sentences.append(current_sentence)
    character_block = []
    character = comment.author.character
    emotion = comment.emotion
    emotion_score = comment.score
    if emotion is None or emotion_score <= emotion_threshold:
      emotion = 'normal'

    character_emotion = random.choice(character_emotions[character][emotion])
    for idx, chunk in enumerate(joined_sentences):
      character_block.append(
        {
          "character": character,
          "name": comment.author.name,
          "text": chunk,
          "emotion": character_emotion,
          "emotion_class": emotion,
          "emotion_class_score": emotion_score
        }
      )
    scene.append(character_block)
  formatted_scenes = []
  last_audio = audio_emotions['normal']
  change_audio = True
  last_emotion = None
  audio_duration = 0
  for character_block in scene:
    scene_objs = []
    character = character_block[0]["character"]
    emotion = character_block[0]["emotion_class"]
    if last_emotion is None:
      last_emotion = emotion
    if emotion in objection_emotions:
      scene_objs.append(
        {
          "character": character,
          "action": Action.OBJECTION,
        }
      )
      if last_audio != audio_emotions['objection']:
        last_audio = audio_emotions['objection']
        change_audio = True
    elif emotion in shake_emotions:
      scene_objs.append(
        {
          "character": character,
          "action": Action.SHAKE_EFFECT,
        }
      )
    elif emotion in hold_it_emotions:
      scene_objs.append(
        {
          "character": character,
          "action": Action.HOLD_IT,
        }
      )
      if last_audio != audio_emotions['holdit']:
        last_audio = audio_emotions['holdit']
        change_audio = True
    elif emotion != last_emotion \
      and audio_duration >= audio_min_scene_duration:
      if last_audio != audio_emotions[emotion]:
        last_audio = audio_emotions[emotion]
        change_audio = True
        last_emotion = emotion

    for obj in character_block:
      scene_objs.append(
        {
          "character": obj["character"],
          "action": Action.TEXT,
          "emotion": obj["emotion"],
          "text": obj["text"],
          "name": obj["name"],
        }
      )
    formatted_scene = {
      "location": character_location_map[character],
      "scene": scene_objs,
    }

    if change_audio:
      formatted_scene["audio"] = last_audio
      change_audio = False
      audio_duration = 0
    audio_duration += 1
    formatted_scenes.append(formatted_scene)
  ace_attorney_animate(formatted_scenes, **kwargs)
