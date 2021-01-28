
import os
import random
import spacy
import string
from textwrap import wrap
from typing import List

import ffmpeg
from pydub import AudioSegment
from tqdm import tqdm
import numpy as np

from animation import animation_cache

from emotions import EmotionModel

from scenes import CharacterBeat, CharacterCue, CharacterShot, CueMusicEffect

from comments import Comment, EmotionComment

from game_themes import Theme


class PhoenixEngine:
  def __init__(
    self,
    theme: Theme,
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

    self.theme = theme

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
      ).overwrite_output().run_async(pipe_stdin=True)
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
      character = self.theme.characters[comment.author.character]
      emotion = comment.emotion
      emotion_score = comment.score
      if emotion is None or emotion_score <= self.emotion_threshold:
        emotion = 'normal'
      # TODO based on emotion_score ?
      character_emotion = random.choice(
        character.emotions[emotion]
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
    last_music = self.theme.emotion_music['normal']
    current_music = last_music
    last_emotion = None
    audio_duration = 0
    for character_cue in character_shot.cues:
      if last_emotion is None:
        last_emotion = character_cue.emotion_class
        character_cue.music = CueMusicEffect(
            music_effect=last_music
          )
      changed_music = False
      if character_cue.emotion_class in self.theme.emotion_actions:
        action = self.theme.emotion_actions[character_cue.emotion_class]
        character_cue.actions.append(action)
        if action.music_effect is not None:
          current_music = action.music_effect
          if current_music != last_music:
            character_cue.music = CueMusicEffect(
              music_effect=current_music
            )
            changed_music = True

      # TODO don't like this very much, work on better music cues
      if not changed_music \
          and character_cue.emotion_class != last_emotion \
              and audio_duration >= self.music_min_scene_duration:
        if character_cue.emotion_class in self.theme.emotion_music:
          current_music = self.theme.emotion_music[character_cue.emotion_class]
          if last_music != current_music:
            character_cue.music = CueMusicEffect(
              music_effect=current_music
            )
            last_emotion = character_cue.emotion_class
            changed_music = True

      if changed_music:
        audio_duration = 0
        last_music = current_music

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
              ).overwrite_output().run_async(pipe_stdin=True)
            )
          process.stdin.write(
            frame_array.astype(np.uint8).tobytes()
          )
    process.stdin.close()
    process.wait()

    animation_cache.clear()

    return video_path

  def _render_audio(self, shot: CharacterShot):

    # loop through all sfx which are not music tracks and combine them into a single track
    # for obj in tqdm(sound_effects, total=len(sound_effects), desc='creating sound effects'):

    sfx_audio = AudioSegment.empty()
    music_audio = AudioSegment.empty()
    music_tracks = []
    # loop through all music tracks and determine their length based on sound effects between them
    for cue in tqdm(shot.cues, total=len(shot.cues), desc='creating sound effects:'):
      cue_length = 0
      for character_sound_effect in cue.sfx:
        cue_length += character_sound_effect.sound_effect.length
        sfx_audio += self.theme.get_character_sfx_audio(character_sound_effect)
      for beat in cue.beats:
        for sound_effect in beat.sfx:
          cue_length += sound_effect.length
          sfx_audio += self.theme.get_sfx_audio(sound_effect)
      if cue.music is not None:
        music_tracks.append(
          cue.music
        )
      if len(music_tracks) > 0:
        music_tracks[-1].length += cue_length

    # create music track based on computed lengths and combine tracks together
    for cue_music_effect in tqdm(music_tracks, total=len(music_tracks), desc='creating music'):
      music_audio += self.theme.get_music_audio(cue_music_effect)

    final_se = sfx_audio.overlay(music_audio)
    audio_path = os.path.join(self.cache_folder, 'audio.mp3')
    final_se.export(audio_path, format="mp3")
    return audio_path

  def _animate_cue(self, cue: CharacterCue):
    location_images, talking_images, text_images = self.theme.animate_cue(cue)

    current_frame = 0
    for action in cue.actions:
      animations, sfx, current_frame = self.theme.animate_action(
        cue,
        action,
        current_frame,
        location_images
      )
      for animation in animations:
        yield animation
      for sound_effect in sfx:
        cue.sfx.append(sound_effect)

    for beat in cue.beats:
      animations, sfx, current_frame = self.theme.animate_beat(
        cue,
        beat,
        current_frame,
        location_images,
        talking_images,
        text_images,
      )
      for animation in animations:
        yield animation
      for sound_effect in sfx:
        beat.sfx.append(sound_effect)
