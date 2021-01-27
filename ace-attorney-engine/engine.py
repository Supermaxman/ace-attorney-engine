
import os
import random
import spacy
import string
from textwrap import wrap
from typing import List, Dict

import ffmpeg
from pydub import AudioSegment
from tqdm import tqdm
import numpy as np

from animation import animation_cache, SceneAnimation

from script_constants import Location, Character, Action, location_map, character_map, character_location_map, \
  audio_emotions, character_emotions, objection_emotions, shake_emotions, hold_it_emotions

from emotions import EmotionModel

from comments import Comment, EmotionComment, Author


class PhoenixEngine(object):
  def __init__(
    self,
    theme='classic',
    emotion_model='mrm8488/t5-base-finetuned-emotion',
    sentence_model='en_core_web_sm',
    emotion_threshold=0.5,
    music_min_scene_duration=4,
    fps=18,
    video_codec='libx264',
    audio_codec='aac',
    video_crf=23,
    lag_frames=25,
    default_animation_length=11,
    scaling_factor=2.0,
    assets_folder='./assets',
    cache_folder='./cache',
  ):
    self.theme = theme
    self.emotion_model = emotion_model
    self.sentence_model = sentence_model
    self.emotion_threshold = emotion_threshold
    self.music_min_scene_duration = music_min_scene_duration
    self.fps = fps
    self.video_codec = video_codec
    self.audio_codec = audio_codec
    self.video_crf = video_crf
    self.lag_frames = lag_frames
    self.default_animation_length = default_animation_length
    self.scaling_factor = scaling_factor
    self.assets_folder = os.path.join(assets_folder, self.theme)
    self.cache_folder = cache_folder
    # mrm8488/t5-base-finetuned-emotion
    self.emo = EmotionModel(
      self.emotion_model
    )

    # en_core_web_sm
    self.nlp = spacy.load(
      sentence_model
    )

  def animate(
    self,
    comments: List[Comment],
    output_filename
  ):
    os.makedirs(os.path.dirname(output_filename), exist_ok=True)

    emotion_comments = self.emo.detect_emotions(comments)

    scene_config = self._configure_scene(emotion_comments)

    if not os.path.exists(self.cache_folder):
      os.mkdir(self.cache_folder)

    sound_effects, video_path = self._render_video(
      scene_config
    )

    audio_path = self._render_audio(
      sound_effects
    )

    video_input = ffmpeg.input(video_path)
    audio_input = ffmpeg.input(audio_path)

    process = (
      ffmpeg.output(
        video_input,
        audio_input,
        output_filename,
        pix_fmt='yuv420p',
        vcodec=self.video_codec,
        r=self.fps,
        acodec=self.audio_codec,
        crf=self.video_crf
      )
        .overwrite_output()
        .run_async(pipe_stdin=True)
    )
    process.wait()

  def _configure_scene(self, comments: List[EmotionComment]):
    # 30 chars per line, 3 lines, but we must subtract 3 for the final potential "..."
    wrap_threshold = (3 * 30) - 3
    scene = []

    for comment in comments:
      tokens = self.nlp(comment.body)
      sentences = [sent.string.strip() for sent in tokens.sents]
      joined_sentences, current_sentence = [], None

      for sentence in sentences:
        if len(sentence) > wrap_threshold:
          text_chunks = []
          text_wrap = wrap(sentence, wrap_threshold)

          for idx, chunk in enumerate(text_wrap):
            if idx != len(text_wrap) - 1 and chunk[-1] not in string.punctuation:
              chunk_text = f"{chunk}..."
            else:
              chunk_text = chunk
            text_chunks.append(chunk_text)
          joined_sentences.extend(text_chunks)
          current_sentence = None
        else:
          if current_sentence is not None and len(current_sentence) + len(sentence) + 1 <= wrap_threshold:
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

      if emotion is None or emotion_score <= self.emotion_threshold:
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
        and audio_duration >= self.music_min_scene_duration:
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
    return formatted_scenes

  def _render_video(self, scene_configs):
    video_path = os.path.join(self.cache_folder, 'video.mp4')
    sound_effects = []
    process = None
    for scene_config in tqdm(scene_configs, desc='creating video', total=len(scene_configs)):
      scene_animations, scene_sfx = self._process_scene(scene_config)
      for animation in scene_animations:
        for frame in animation.frames:
          frame_array = np.array(frame)[:, :, :3]
          if process is None:
            height, width, channels = frame_array.shape
            video_input = ffmpeg.input(
              'pipe:',
              format='rawvideo',
              pix_fmt='rgb24',
              s=f'{width}x{height}',
              r=self.fps
            )
            process = (
              ffmpeg.output(
                video_input,
                video_path,
                pix_fmt='yuv420p',
                vcodec=self.video_codec,
                r=self.fps,
                crf=self.video_crf
              )
                .overwrite_output()
                .run_async(pipe_stdin=True)
            )
          process.stdin.write(
            frame_array.astype(np.uint8).tobytes()
          )
      sound_effects.extend(scene_sfx)
    process.stdin.close()
    process.wait()

    animation_cache.clear()

    return sound_effects, video_path

  def _render_audio(self, sound_effects: List[Dict]):
    audio_se = AudioSegment.empty()
    bip = AudioSegment.from_wav(
      f"{self.assets_folder}/sfx general/sfx-blipmale.wav"
    ) + AudioSegment.silent(duration=50)
    blink = AudioSegment.from_wav(f"{self.assets_folder}/sfx general/sfx-blink.wav")
    blink -= 10
    badum = AudioSegment.from_wav(f"{self.assets_folder}/sfx general/sfx-fwashing.wav")
    long_bip = bip * 100
    long_bip -= 10
    spf = 1 / self.fps * 1000
    pheonix_objection = AudioSegment.from_mp3(f"{self.assets_folder}/Phoenix - objection.mp3")
    edgeworth_objection = AudioSegment.from_mp3(
      f"{self.assets_folder}/Edgeworth - (English) objection.mp3"
    )
    default_objection = AudioSegment.from_mp3(f"{self.assets_folder}/Payne - Objection.mp3")

    # loop through all sfx which are not music tracks and combine them into a single track
    for obj in tqdm(sound_effects, total=len(sound_effects), desc='creating sound effects'):
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
    for track in tqdm(music_tracks, total=len(music_tracks), desc='creating music'):
      track_length = track["length"]
      track_duration = int(track_length * spf)
      music_se += AudioSegment.from_mp3(track["src"])[:track_duration]

    final_se = audio_se.overlay(music_se)
    audio_path = os.path.join(self.cache_folder, 'audio.mp3')
    final_se.export(audio_path, format="mp3")
    return audio_path

  def _process_scene(self, scene):
    sound_effects = []
    scene_animations = []
    bg = animation_cache.get_anim_img(
      f'{self.assets_folder}/{location_map[scene["location"]]}',
      scaling_factor=self.scaling_factor
    )
    arrow = animation_cache.get_anim_img(
      f"{self.assets_folder}/arrow.png",
      x=235,
      y=170,
      w=15,
      h=15,
      key_x=5,
      scaling_factor=self.scaling_factor
    )
    textbox = animation_cache.get_anim_img(
      f"{self.assets_folder}/textbox4.png",
      w=bg.w // self.scaling_factor,
      scaling_factor=self.scaling_factor
    )
    name_text_font_size = 10
    name_text_x = 4
    name_text_y = 115
    text_box_font_size = 15
    text_box_x = 5
    text_box_y = 130
    text_box_max_line_count = 32
    bench = None

    if scene["location"] == Location.COURTROOM_LEFT:
      bench = animation_cache.get_anim_img(
        f"{self.assets_folder}/logo-left.png",
        scaling_factor=self.scaling_factor
      )
    elif scene["location"] == Location.COURTROOM_RIGHT:
      bench = animation_cache.get_anim_img(
        f"{self.assets_folder}/logo-right.png",
        scaling_factor=self.scaling_factor
      )
    elif scene["location"] == Location.WITNESS_STAND:
      bench = animation_cache.get_anim_img(
        f"{self.assets_folder}/witness_stand.png",
        w=bg.w // self.scaling_factor,
        scaling_factor=self.scaling_factor
      )
      bench.y = bg.h - bench.h

    if "audio" in scene:
      sound_effects.append({"_type": "bg", "src": f'{self.assets_folder}/{scene["audio"]}.mp3'})

    current_frame = 0
    current_character_name = None
    text = None

    for obj in scene["scene"]:
      if "character" in obj:
        _dir = f'{self.assets_folder}/{character_map[obj["character"]]}'
        current_character_name = str(obj["character"])
        character_name = animation_cache.get_anim_text(
          current_character_name,
          font_path=f"{self.assets_folder}/igiari/Igiari.ttf",
          font_size=name_text_font_size,
          x=name_text_x,
          y=name_text_y,
          scaling_factor=self.scaling_factor
        )
        default = "normal" if "emotion" not in obj else obj["emotion"]
        default_path = (
          f"{_dir}/{current_character_name.lower()}-{default}(a).gif"
        )

        if not os.path.isfile(default_path):
          default_path = (
            f"{_dir}/{current_character_name.lower()}-{default}.gif"
          )

        default_character = animation_cache.get_anim_img(
          default_path,
          half_speed=True,
          scaling_factor=self.scaling_factor
        )

        if "(a)" in default_path:
          talking_character = animation_cache.get_anim_img(
            default_path.replace("(a)", "(b)"),
            half_speed=True,
            scaling_factor=self.scaling_factor
          )
        else:
          talking_character = animation_cache.get_anim_img(
            default_path,
            half_speed=True,
            scaling_factor=self.scaling_factor
          )

      if "emotion" in obj:
        default = obj["emotion"]
        default_path = (
          f"{_dir}/{current_character_name.lower()}-{default}(a).gif"
        )

        if not os.path.isfile(default_path):
          default_path = (
            f"{_dir}/{current_character_name.lower()}-{default}.gif"
          )

        default_character = animation_cache.get_anim_img(
          default_path,
          half_speed=True,
          scaling_factor=self.scaling_factor
        )

        if "(a)" in default_path:
          talking_character = animation_cache.get_anim_img(
            default_path.replace("(a)", "(b)"),
            half_speed=True,
            scaling_factor=self.scaling_factor
          )
        else:
          talking_character = animation_cache.get_anim_img(
            default_path,
            half_speed=True,
            scaling_factor=self.scaling_factor
          )

      if "action" in obj and (
        obj["action"] == Action.TEXT
        or obj["action"] == Action.TEXT_SHAKE_EFFECT
      ):
        character = talking_character
        _text = split_str_into_newlines(obj["text"], text_box_max_line_count)
        _colour = None if "colour" not in obj else obj["colour"]
        text = animation_cache.get_anim_text(
          _text,
          font_path=f"{self.assets_folder}/igiari/Igiari.ttf",
          font_size=text_box_font_size,
          x=text_box_x,
          y=text_box_y,
          typewriter_effect=True,
          colour=_colour,
          scaling_factor=self.scaling_factor
        )
        num_frames = len(_text) + self.lag_frames
        _character_name = character_name

        if "name" in obj:
          _character_name = animation_cache.get_anim_text(
            obj["name"],
            font_path=f"{self.assets_folder}/igiari/Igiari.ttf",
            font_size=name_text_font_size,
            x=name_text_x,
            y=name_text_y,
            scaling_factor=self.scaling_factor
          )

        if obj["action"] == Action.TEXT_SHAKE_EFFECT:
          bg.shake_effect = True
          character.shake_effect = True

          if bench is not None:
            bench.shake_effect = True

          textbox.shake_effect = True

        scene_animations.append(
          SceneAnimation(
            [bg, character, bench, textbox, _character_name, text],
            length=len(_text) - 1,
            start_frame=current_frame
          )
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
        scene_animations.append(
          SceneAnimation(
            [bg, character, bench, textbox, _character_name, text, arrow],
            length=self.lag_frames,
            start_frame=len(_text) - 1
          )
        )
        current_frame += num_frames
        sound_effects.append({"_type": "silence", "length": self.lag_frames})

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

        scene_animations.append(
          SceneAnimation(
            scene_objs,
            length=self.lag_frames,
            start_frame=current_frame
          )
        )
        sound_effects.append({"_type": "shock", "length": self.lag_frames})
        current_frame += self.lag_frames
        bg.shake_effect = False
        character.shake_effect = False

        if bench is not None:
          bench.shake_effect = False

        textbox.shake_effect = False

      elif "action" in obj and obj["action"] == Action.OBJECTION:
        effect_image = animation_cache.get_anim_img(
          f"{self.assets_folder}/objection.gif",
          shake_effect=True,
          scaling_factor=self.scaling_factor
        )
        character = default_character
        scene_animations.append(
          SceneAnimation(
            [bg, character, bench, effect_image],
            length=self.default_animation_length,
            start_frame=current_frame
          )
        )
        scene_animations.append(
          SceneAnimation(
            [bg, character, bench],
            length=self.default_animation_length,
            start_frame=current_frame
          )
        )

        sound_effects.append(
          {
            "_type": "objection",
            "character": current_character_name.lower(),
            "length": 2 * self.default_animation_length,
          }
        )
        current_frame += self.default_animation_length

      elif "action" in obj and obj["action"] == Action.HOLD_IT:
        effect_image = animation_cache.get_anim_img(
          f"{self.assets_folder}/holdit.gif",
          shake_effect=True,
          scaling_factor=self.scaling_factor
        )
        character = default_character
        scene_animations.append(
          SceneAnimation(
            [bg, character, bench, effect_image],
            length=self.default_animation_length,
            start_frame=current_frame
          )
        )
        scene_animations.append(
          SceneAnimation(
            [bg, character, bench],
            length=self.default_animation_length,
            start_frame=current_frame
          )
        )
        sound_effects.append(
          {
            "_type": "objection",
            "character": current_character_name.lower(),
            "length": 2 * self.default_animation_length,
          }
        )
        current_frame += self.default_animation_length

      else:
        character = default_character
        _length = self.lag_frames

        if "length" in obj:
          _length = obj["length"]
        if "repeat" in obj:
          character.repeat = obj["repeat"]

        scene_animations.append(
          SceneAnimation(
            [bg, character, bench],
            length=_length,
            start_frame=current_frame
          )
        )
        character.repeat = True
        sound_effects.append({"_type": "silence", "length": _length})
        current_frame += _length

    return scene_animations, sound_effects

  def get_characters(self, most_common: List):
    # this may be based on theme in the future, don't make static
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


def split_str_into_newlines(text: str, max_line_count):
  lines = []
  for line in wrap(text, max_line_count):
    lines.append(line + ' ')
  new_text = '\n'.join(lines)
  return new_text
