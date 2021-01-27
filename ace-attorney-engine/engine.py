
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
  audio_emotions, character_emotions, \
  action_music, action_emotions

from emotions import EmotionModel

from scenes import CharacterBeat, CharacterCue, CharacterShot, SoundEffect, MusicEffect

from comments import Comment, EmotionComment, Author


class PhoenixEngine:
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
    # TODO make parameter?
    self.wrap_threshold = (3 * 30) - 3

  def animate(
    self,
    comments: List[Comment],
    output_filename
  ):
    os.makedirs(os.path.dirname(output_filename), exist_ok=True)

    emotion_comments = self.emo.detect_emotions(comments)

    shot = self._create_shot(emotion_comments)

    if not os.path.exists(self.cache_folder):
      os.mkdir(self.cache_folder)

    video_path = self._render_video(
      shot
    )

    audio_path = self._render_audio(
      shot
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

  def _parse_comment(self, comment: EmotionComment):
    tokens = self.nlp(comment.body)
    sentences = [sent.string.strip() for sent in tokens.sents]
    joined_sentences, current_sentence = [], None

    for sentence in sentences:
      if len(sentence) > self.wrap_threshold:
        text_chunks = []
        text_wrap = wrap(sentence, self.wrap_threshold)

        for idx, chunk in enumerate(text_wrap):
          if idx != len(text_wrap) - 1 and chunk[-1] not in string.punctuation:
            chunk_text = f"{chunk}..."
          else:
            chunk_text = chunk
          text_chunks.append(chunk_text)
        joined_sentences.extend(text_chunks)
        current_sentence = None
      else:
        if current_sentence is not None and len(current_sentence) + len(sentence) + 1 <= self.wrap_threshold:
          current_sentence += " " + sentence
        else:
          if current_sentence is not None:
            joined_sentences.append(current_sentence)
          current_sentence = sentence

    if current_sentence is not None:
      joined_sentences.append(current_sentence)
    return joined_sentences

  def _parse_shot(self, comments: List[EmotionComment]) -> CharacterShot:
    character_cues = []

    for comment in comments:
      text_blocks = self._parse_comment(comment)
      character = comment.author.character
      emotion = comment.emotion
      emotion_score = comment.score
      if emotion is None or emotion_score <= self.emotion_threshold:
        emotion = 'normal'
      # TODO based on emotion_score ?
      character_emotion = random.choice(
        character_emotions[character][emotion]
      )

      character_beats = []
      for idx, text_block in enumerate(text_blocks):
        character_beat = CharacterBeat(
          text=text_block,
        )
        character_beats.append(
          character_beat
        )
      character_cue = CharacterCue(
        character=character,
        name=comment.author.name,
        beats=character_beats,
        location=character_location_map[character],
        emotion=character_emotion,
        emotion_class=emotion,
        emotion_class_score=emotion_score
      )

      character_cues.append(character_cue)
    character_shot = CharacterShot(
      cues=character_cues
    )
    return character_shot

  def _create_shot(self, comments: List[EmotionComment]):
    # 30 chars per line, 3 lines, but we must subtract 3 for the final potential "..."
    character_shot = self._parse_shot(comments)
    last_audio = audio_emotions['normal']
    current_audio = last_audio
    last_emotion = None
    audio_duration = 0
    for character_cue in character_shot.cues:
      if last_emotion is None:
        last_emotion = character_cue.emotion_class
        character_cue.music = MusicEffect(
          track=last_audio
        )
      changed_music = False
      for action, emotions_set in action_emotions.items():
        if character_cue.emotion_class in emotions_set:
          character_cue.actions.append(action)
          if action in action_music:
            current_audio = action_music[action]
            if current_audio != last_audio:
              character_cue.music = MusicEffect(
                track=current_audio
              )
              changed_music = True
          break
      # TODO don't like this very much, work on better music cues
      if not changed_music \
          and character_cue.emotion_class != last_emotion \
              and audio_duration >= self.music_min_scene_duration:
        current_audio = audio_emotions[character_cue.emotion_class]
        if last_audio != current_audio:
          character_cue.music = MusicEffect(
              track=current_audio
            )
          last_emotion = character_cue.emotion_class
          changed_music = True

      if changed_music:
        audio_duration = 0
        last_audio = current_audio

      audio_duration += 1

    return character_shot

  def _render_video(self, shot: CharacterShot):
    video_path = os.path.join(self.cache_folder, 'video.mp4')
    process = None
    for cue in tqdm(shot.cues, desc='creating video', total=len(shot.cues)):
      for animation in self._animate_cue(cue):
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
    process.stdin.close()
    process.wait()

    animation_cache.clear()

    return video_path

  def _render_audio(self, shot: CharacterShot):
    bip = AudioSegment.from_wav(
      f"{self.assets_folder}/sfx general/sfx-blipmale.wav"
    ) + AudioSegment.silent(duration=50)
    blink = AudioSegment.from_wav(
      f"{self.assets_folder}/sfx general/sfx-blink.wav"
    )
    blink -= 10
    badum = AudioSegment.from_wav(
      f"{self.assets_folder}/sfx general/sfx-fwashing.wav"
    )
    long_bip = bip * 100
    long_bip -= 10
    spf = 1 / self.fps * 1000
    pheonix_objection = AudioSegment.from_mp3(
      f"{self.assets_folder}/Phoenix - objection.mp3"
    )
    edgeworth_objection = AudioSegment.from_mp3(
      f"{self.assets_folder}/Edgeworth - (English) objection.mp3"
    )
    default_objection = AudioSegment.from_mp3(
      f"{self.assets_folder}/Payne - Objection.mp3"
    )

    # loop through all sfx which are not music tracks and combine them into a single track
    # for obj in tqdm(sound_effects, total=len(sound_effects), desc='creating sound effects'):

    def get_sfx_audio(se):
      se_duration = int(se.length * spf)
      if se.type == "silence":
        se_audio = AudioSegment.silent(duration=se_duration)
      elif se.type == "bip":
        se_duration -= len(blink)
        se_audio = blink + long_bip[:se_duration]
      elif se.type == "objection":
        obj_character = se.character
        if obj_character == "phoenix":
          se_audio = pheonix_objection[:se_duration]
        elif obj_character == "edgeworth":
          se_audio = edgeworth_objection[:se_duration]
        else:
          se_audio = default_objection[:se_duration]
      elif se.type == "shock":
        se_audio = badum[:se_duration]
      else:
        raise ValueError(f'Unknown sound effect type: {se.type}')
      return se_audio

    sfx_audio = AudioSegment.empty()
    music_audio = AudioSegment.empty()
    music_tracks = []
    # loop through all music tracks and determine their length based on sound effects between them
    for cue in tqdm(shot.cues, total=len(shot.cues), desc='creating sound effects:'):
      cue_length = 0
      for sound_effect in cue.sfx:
        cue_length += sound_effect.length
        sfx_audio += get_sfx_audio(sound_effect)
      for beat in cue.beats:
        for sound_effect in beat.sfx:
          cue_length += sound_effect.length
          sfx_audio += get_sfx_audio(sound_effect)
      if cue.music is not None:
        music_tracks.append(
          cue.music
        )
      if len(music_tracks) > 0:
        music_tracks[-1].length += cue_length

    # create music track based on computed lengths and combine tracks together
    for music_effect in tqdm(music_tracks, total=len(music_tracks), desc='creating music'):
      track_length = music_effect.length
      track_duration = int(track_length * spf)
      track_path = f'{self.assets_folder}/{music_effect.track}.mp3'
      music_audio += AudioSegment.from_mp3(track_path)[:track_duration]

    final_se = sfx_audio.overlay(music_audio)
    audio_path = os.path.join(self.cache_folder, 'audio.mp3')
    final_se.export(audio_path, format="mp3")
    return audio_path

  def _animate_cue(self, cue: CharacterCue):
    bg = animation_cache.get_anim_img(
      f'{self.assets_folder}/{location_map[cue.location]}',
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

    if cue.location == Location.COURTROOM_LEFT:
      bench = animation_cache.get_anim_img(
        f"{self.assets_folder}/logo-left.png",
        scaling_factor=self.scaling_factor
      )
    elif cue.location == Location.COURTROOM_RIGHT:
      bench = animation_cache.get_anim_img(
        f"{self.assets_folder}/logo-right.png",
        scaling_factor=self.scaling_factor
      )
    elif cue.location == Location.WITNESS_STAND:
      bench = animation_cache.get_anim_img(
        f"{self.assets_folder}/witness_stand.png",
        w=bg.w // self.scaling_factor,
        scaling_factor=self.scaling_factor
      )
      bench.y = bg.h - bench.h

    character_path = f'{self.assets_folder}/{character_map[cue.character]}'
    current_character_name = str(cue.character)

    character_emotion_path = (
      f"{character_path}/{current_character_name.lower()}-{cue.emotion}(a).gif"
    )

    if not os.path.isfile(character_emotion_path):
      character_emotion_path = (
        f"{character_path}/{current_character_name.lower()}-{cue.emotion}.gif"
      )

    default_character = animation_cache.get_anim_img(
      character_emotion_path,
      half_speed=True,
      scaling_factor=self.scaling_factor
    )

    if "(a)" in character_emotion_path:
      character_emotion_path = character_emotion_path.replace("(a)", "(b)")

    talking_character = animation_cache.get_anim_img(
      character_emotion_path,
      half_speed=True,
      scaling_factor=self.scaling_factor
    )

    character_name = animation_cache.get_anim_text(
      cue.name,
      font_path=f"{self.assets_folder}/igiari/Igiari.ttf",
      font_size=name_text_font_size,
      x=name_text_x,
      y=name_text_y,
      scaling_factor=self.scaling_factor
    )

    current_frame = 0

    for action in cue.actions:
      if action == Action.SHAKE_EFFECT:
        bg.shake_effect = True
        default_character.shake_effect = True

        if bench is not None:
          bench.shake_effect = True

        textbox.shake_effect = True

        yield (
          SceneAnimation(
            [bg, default_character, bench],
            length=self.lag_frames,
            start_frame=current_frame
          )
        )
        cue.sfx.append(
          SoundEffect(
            type='shock',
            length=self.lag_frames
          )
        )

        current_frame += self.lag_frames
        bg.shake_effect = False
        default_character.shake_effect = False

        if bench is not None:
          bench.shake_effect = False

        textbox.shake_effect = False
      elif action == Action.OBJECTION:
        effect_image = animation_cache.get_anim_img(
          f"{self.assets_folder}/objection.gif",
          shake_effect=True,
          scaling_factor=self.scaling_factor
        )
        yield (
          SceneAnimation(
            [bg, default_character, bench, effect_image],
            length=self.default_animation_length,
            start_frame=current_frame
          )
        )
        yield (
          SceneAnimation(
            [bg, default_character, bench],
            length=self.default_animation_length,
            start_frame=current_frame
          )
        )
        cue.sfx.append(
          SoundEffect(
            type='objection',
            length=2 * self.default_animation_length,
            character=current_character_name.lower()
          )
        )
        current_frame += self.default_animation_length
      elif action == Action.HOLD_IT:
        effect_image = animation_cache.get_anim_img(
          f"{self.assets_folder}/holdit.gif",
          shake_effect=True,
          scaling_factor=self.scaling_factor
        )
        character = default_character
        yield (
          SceneAnimation(
            [bg, character, bench, effect_image],
            length=self.default_animation_length,
            start_frame=current_frame
          )
        )
        yield (
          SceneAnimation(
            [bg, character, bench],
            length=self.default_animation_length,
            start_frame=current_frame
          )
        )
        cue.sfx.append(
          SoundEffect(
            type='objection',
            length=2 * self.default_animation_length,
            character=current_character_name.lower(),
          )
        )

        current_frame += self.default_animation_length

    for beat in cue.beats:
      _text = split_str_into_newlines(beat.text, text_box_max_line_count)
      _colour = None

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

      # if obj["action"] == Action.TEXT_SHAKE_EFFECT:
      #   bg.shake_effect = True
      #   character.shake_effect = True
      #
      #   if bench is not None:
      #     bench.shake_effect = True
      #
      #   textbox.shake_effect = True

      yield (
        SceneAnimation(
          [bg, talking_character, bench, textbox, character_name, text],
          length=len(_text) - 1,
          start_frame=current_frame
        )
      )
      beat.sfx.append(
        SoundEffect(
          type='bip',
          length=len(_text) - 1
        )
      )

      # if obj["action"] == Action.TEXT_SHAKE_EFFECT:
      #   bg.shake_effect = False
      #   character.shake_effect = False
      #
      #   if bench is not None:
      #     bench.shake_effect = False
      #
      #   textbox.shake_effect = False

      text.typewriter_effect = False
      yield (
        SceneAnimation(
          [bg, default_character, bench, textbox, character_name, text, arrow],
          length=self.lag_frames,
          start_frame=len(_text) - 1
        )
      )

      current_frame += num_frames
      beat.sfx.append(
        SoundEffect(
          type='silence',
          length=self.lag_frames
        )
      )

      # length = self.lag_frames
      #
      # if "length" in obj:
      #   length = obj["length"]
      # if "repeat" in obj:
      #   default_character.repeat = obj["repeat"]
      #
      # yield (
      #   SceneAnimation(
      #     [bg, default_character, bench],
      #     length=length,
      #     start_frame=current_frame
      #   )
      # )
      # default_character.repeat = True
      #
      # beat.sfx.append(
      #   SoundEffect(
      #     type='silence',
      #     length=length
      #   )
      # )
      # current_frame += length

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
