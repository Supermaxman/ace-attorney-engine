
import os
from enum import IntEnum
from typing import List, Dict
from textwrap import wrap
from dataclasses import dataclass
from pydub import AudioSegment

from scenes import Action, SoundEffect, MusicEffect, Character, Location, CharacterCue, CharacterSoundEffect, \
  CharacterBeat

from animation import animation_cache, SceneAnimation


class ClassicTheme:
  theme = 'classic'

  class Location(IntEnum):
    COURTROOM_LEFT = 1
    WITNESS_STAND = 2
    COURTROOM_RIGHT = 3
    CO_COUNCIL = 4
    JUDGE_STAND = 5
    COURT_HOUSE = 6

  def __init__(self, assets_folder, scaling_factor):
    self.assets_folder = os.path.join(assets_folder, self.theme)
    self.default_animation_length = 11
    self.lag_frames = 25
    self.text_box_max_line_count = 32
    self.fps = 18
    self.scaling_factor = scaling_factor

    self.actions = [
      Action(
        length=self.default_animation_length,
        asset_name='objection.gif',
        sound_effect=SoundEffect(
          type='objection',
          length=2 * self.default_animation_length
        ),
        music_effect=MusicEffect(
          track='08 - Pressing Pursuit _ Cornered'
        ),
        emotion_triggers={'anger'}
      ),
      Action(
        length=self.default_animation_length,
        asset_name='holdit.gif',
        # TODO get holdit sfx
        sound_effect=SoundEffect(
          type='objection',
          length=2 * self.default_animation_length
        ),
        music_effect=MusicEffect(
          track='11 - Pressing Pursuit _ Cornered , Variation'
        ),
        emotion_triggers={'surprise'}
      ),
      Action(
        length=self.lag_frames,
        shake_effect=True,
        sound_effect=SoundEffect(
          type='shock',
          length=self.lag_frames
        ),
        emotion_triggers={'joy'}
      ),
    ]

    self.emotion_actions = {}
    for action in self.actions:
      for emotion in action.emotion_triggers:
        if emotion in self.emotion_actions:
          print('WARNING: overlapping emotion action triggers!')
        self.emotion_actions[emotion] = action

    # sadness
    # joy
    # love
    # anger
    # fear
    # surprise
    self.emotion_music = {
      "normal": MusicEffect(
        track="03 - Turnabout Courtroom - Trial",
      ),
      "sadness": MusicEffect(
        track="10 - Suspense",
      ),
      "joy": MusicEffect(
        track="03 - Turnabout Courtroom - Trial",
      ),
      "love": MusicEffect(
        track="05 - Logic and Trick",
      ),
      "anger": MusicEffect(
        track="11 - Pressing Pursuit _ Cornered , Variation",
      ),
      "fear": MusicEffect(
        track="10 - Suspense",
      ),
      "surprise": MusicEffect(
        track="05 - Logic and Trick",
      ),
    }

    self.locations = {
      self.Location.COURTROOM_LEFT: Location(
        name='COURTROOM_LEFT',
        asset_name='defenseempty.png',
        extra_assets=['logo-left.png']
      ),
      self.Location.WITNESS_STAND: Location(
        name='WITNESS_STAND',
        asset_name='witnessempty.png',
        extra_assets=['witness_stand.png']
      ),
      self.Location.COURTROOM_RIGHT: Location(
        name='COURTROOM_RIGHT',
        asset_name='prosecutorempty.png',
        extra_assets=['logo-right.png']
      ),
      self.Location.CO_COUNCIL: Location(
        name='CO_COUNCIL',
        asset_name='helperstand.png'
      ),
      self.Location.JUDGE_STAND: Location(
        name='JUDGE_STAND',
        asset_name='judgestand.png'
      ),
      self.Location.COURT_HOUSE: Location(
        name='COURT_HOUSE',
        asset_name='courtroomoverview.png'
      ),
    }

    self.characters = {
      self.Character.PHOENIX: Character(
        name='Phoenix',
        emotions={
          "sadness": ["emo"],
          "joy": ["confident", "pointing"],
          "love": ["confident", "pointing"],
          "anger": ["handsondesk"],
          "fear": ["emo", "sweating", "sheepish"],
          "surprise": ["handsondesk"],
          "normal": ["document", "normal", "thinking", "coffee"]
        },
        location=self.locations[self.Location.COURTROOM_LEFT],
        asset_name='Sprites-phoenix'
      ),
      self.Character.EDGEWORTH: Character(
        name='Edgeworth',
        emotions={
          "sadness": ["emo"],
          "joy": ["confident", "pointing"],
          "love": ["smirk"],
          "anger": ["handondesk"],
          "fear": ["emo"],
          "surprise": ["handondesk"],
          "normal": ["document", "normal", "thinking"]
        },
        location=self.locations[self.Location.COURTROOM_RIGHT],
        asset_name='Sprites-edgeworth'
      ),
      self.Character.GODOT: Character(
        name='Godot',
        emotions={
          "sadness": ["steams"],
          "joy": ["normal"],
          "love": ["normal"],
          "anger": ["pointing"],
          "fear": ["steams"],
          "surprise": ["steams"],
          "normal": ["normal"],
        },
        location=self.locations[self.Location.COURTROOM_RIGHT],
        asset_name='Sprites-Godot'
      ),
      self.Character.FRANZISKA: Character(
        name='Franziska',
        emotions={
          "sadness": ["sweating"],
          "joy": ["ha"],
          "love": ["ha"],
          "anger": ["mad"],
          "fear": ["sweating"],
          "surprise": ["withwhip"],
          "normal": ["ready"],
        },
        location=self.locations[self.Location.COURTROOM_RIGHT],
        asset_name='Sprites-franziska'
      ),
      self.Character.JUDGE: Character(
        name='Judge',
        emotions={
          "sadness": ["headshake"],
          "joy": ["normal"],
          "love": ["nodding"],
          "anger": ["warning"],
          "fear": ["warning"],
          "surprise": ["warning"],
          "normal": ["normal"],
        },
        location=self.locations[self.Location.JUDGE_STAND],
        asset_name='Sprites-judge'
      ),
      self.Character.LARRY: Character(
        name='Larry',
        emotions={
          "sadness": ["extra"],
          "joy": ["hello"],
          "love": ["hello"],
          "anger": ["mad"],
          "fear": ["nervous"],
          "surprise": ["nervous"],
          "normal": ["normal"],
        },
        location=self.locations[self.Location.WITNESS_STAND],
        asset_name='Sprites-larry'
      ),
      self.Character.MAYA: Character(
        name='Maya',
        emotions={
          "sadness": ["bench-strict", "bench-ugh"],
          "joy": ["bench-hum"],
          "love": ["bench"],
          "anger": ["bench-strict"],
          "fear": ["bench-ugh"],
          "surprise": ["bench-hum"],
          "normal": ["bench-profile"],
        },
        location=self.locations[self.Location.CO_COUNCIL],
        asset_name='Sprites-maya'
      ),
      self.Character.KARMA: Character(
        name='Karma',
        emotions={
          "sadness": ["badmood"],
          "joy": ["normal"],
          "love": ["smirk", "snap"],
          "anger": ["break"],
          "fear": ["sweat"],
          "surprise": ["break"],
          "normal": ["normal"],
        },
        location=self.locations[self.Location.COURTROOM_RIGHT],
        asset_name='Sprites-karma'
      ),
      self.Character.PAYNE: Character(
        name='Payne',
        emotions={
          "sadness": ["sweating"],
          "joy": ["normal"],
          "love": ["confident"],
          "anger": ["sweating"],
          "fear": ["sweating"],
          "surprise": ["sweating"],
          "normal": ["normal"],
        },
        location=self.locations[self.Location.COURTROOM_RIGHT],
        asset_name='Sprites-payne'
      ),
      self.Character.MAGGEY: Character(
        name='Maggey',
        emotions={
          "sadness": ["sad"],
          "joy": ["pumped"],
          "love": ["shining"],
          "anger": ["sad"],
          "fear": ["sad"],
          "surprise": ["sad"],
          "normal": ["normal"],
        },
        location=self.locations[self.Location.WITNESS_STAND],
        asset_name='Sprites-Maggey'
      ),
      self.Character.PEARL: Character(
        name='Pearl',
        emotions={
          "sadness": ["cries"],
          "joy": ["sparkle"],
          "love": ["sparkle"],
          "anger": ["fight", "disappointed"],
          "fear": ["cries"],
          "surprise": ["surprised"],
          "normal": ["normal", "thinking", "shy"],
        },
        location=self.locations[self.Location.WITNESS_STAND],
        asset_name='Sprites-Pearl'
      ),
      self.Character.LOTTA: Character(
        name='Lotta',
        emotions={
          "sadness": ["badmood"],
          "joy": ["confident", "smiling"],
          "love": ["confident", "smiling"],
          "anger": ["mad", "disappointed"],
          "fear": ["badmood"],
          "surprise": ["mad"],
          "normal": ["normal", "shy", "thinking"],
        },
        location=self.locations[self.Location.WITNESS_STAND],
        asset_name='Sprites-lotta'
      ),
      self.Character.GUMSHOE: Character(
        name='Gumshoe',
        emotions={
          "sadness": ["disheartened"],
          "joy": ["side"],
          "love": ["laughing", "confident", "pumped"],
          "anger": ["mad"],
          "fear": ["disheartened"],
          "surprise": ["disheartened"],
          "normal": ["normal", "side", "thinking"],
        },
        location=self.locations[self.Location.WITNESS_STAND],
        asset_name='Sprites-gumshoe'
      ),
      self.Character.GROSSBERG: Character(
        name='Grossberg',
        emotions={
          "sadness": ["sweating"],
          "joy": ["normal"],
          "love": ["normal"],
          "anger": ["sweating"],
          "fear": ["sweating"],
          "surprise": ["sweating"],
          "normal": ["normal"],
        },
        location=self.locations[self.Location.WITNESS_STAND],
        asset_name='Sprites-grossberg'
      ),
    }

    self.arrow = animation_cache.get_anim_img(
      os.path.join(self.assets_folder, 'arrow.png'),
      x=235,
      y=170,
      w=15,
      h=15,
      key_x=5,
      scaling_factor=self.scaling_factor
    )
    # 1000 ms in a second
    self.spf = 1 / self.fps * 1000

    # TODO revamp audio system to load these
    self.bip = AudioSegment.from_wav(
      f"{self.assets_folder}/sfx general/sfx-blipmale.wav"
    ) + AudioSegment.silent(duration=50)
    self.blink = AudioSegment.from_wav(
      f"{self.assets_folder}/sfx general/sfx-blink.wav"
    )
    self.blink -= 10
    self.badum = AudioSegment.from_wav(
      f"{self.assets_folder}/sfx general/sfx-fwashing.wav"
    )
    self.long_bip = self.bip * 100
    self.long_bip -= 10

    # TODO pair these sfx with characters
    self.phoenix_objection = AudioSegment.from_mp3(
      f"{self.assets_folder}/Phoenix - objection.mp3"
    )
    self.edgeworth_objection = AudioSegment.from_mp3(
      f"{self.assets_folder}/Edgeworth - (English) objection.mp3"
    )
    self.default_objection = AudioSegment.from_mp3(
      f"{self.assets_folder}/Payne - Objection.mp3"
    )

  def get_sfx_audio(self, se):
    se_duration = int(se.length * self.spf)
    if se.type == "silence":
      se_audio = AudioSegment.silent(duration=se_duration)
    elif se.type == "bip":
      se_duration -= len(self.blink)
      se_audio = self.blink + self.long_bip[:se_duration]
    else:
      raise ValueError(f'Unknown sound effect type: {se.type}')
    return se_audio

  def get_character_sfx_audio(self, character_se):
    se = character_se.sound_effect
    se_duration = int(se.length * self.spf)
    if se.type == "objection":
      obj_character = character_se.character.name.lower()
      if obj_character == "phoenix":
        se_audio = self.phoenix_objection[:se_duration]
      elif obj_character == "edgeworth":
        se_audio = self.edgeworth_objection[:se_duration]
      else:
        se_audio = self.default_objection[:se_duration]
    elif se.type == "shock":
      se_audio = self.badum[:se_duration]
    else:
      raise ValueError(f'Unknown character sound effect type: {se.type}')
    return se_audio

  def get_music_audio(self, cue_music_effect):
    track_duration = int(cue_music_effect.length * self.spf)
    track_path = f'{self.assets_folder}/{cue_music_effect.music_effect.track}.mp3'
    music_audio = AudioSegment.from_mp3(track_path)[:track_duration]
    return music_audio

  def animate_cue(self, cue: CharacterCue):
    location_images = []
    talking_images = []
    bg = animation_cache.get_anim_img(
      os.path.join(self.assets_folder, cue.character.location.asset_name),
      scaling_factor=self.scaling_factor
    )
    location_images.append(bg)
    talking_images.append(bg)

    character_path = os.path.join(self.assets_folder, cue.character.asset_name)

    character_emotion_path = (
      os.path.join(character_path, f'{cue.character.name.lower()}-{cue.emotion}(a).gif')
    )

    if not os.path.isfile(character_emotion_path):
      character_emotion_path = (
        os.path.join(character_path, f'{cue.character.name.lower()}-{cue.emotion}.gif')
      )

    default_character = animation_cache.get_anim_img(
      character_emotion_path,
      half_speed=True,
      scaling_factor=self.scaling_factor
    )

    location_images.append(default_character)

    if "(a)" in character_emotion_path:
      character_emotion_path = character_emotion_path.replace("(a)", "(b)")

    talking_character = animation_cache.get_anim_img(
      character_emotion_path,
      half_speed=True,
      scaling_factor=self.scaling_factor
    )
    talking_images.append(talking_character)

    for extra_asset in cue.character.location.extra_assets:
      w = None
      if extra_asset == 'witness_stand.png':
        w = bg.w // self.scaling_factor
      bench = animation_cache.get_anim_img(
        os.path.join(self.assets_folder, extra_asset),
        w=w,
        scaling_factor=self.scaling_factor
      )
      if w is not None:
        bench.y = bg.h - bench.h
      location_images.append(bench)
      talking_images.append(bench)

    textbox = animation_cache.get_anim_img(
      os.path.join(self.assets_folder, 'textbox4.png'),
      w=bg.w // self.scaling_factor,
      scaling_factor=self.scaling_factor
    )

    character_name = animation_cache.get_anim_text(
      cue.name,
      font_path=os.path.join(self.assets_folder, 'igiari', 'Igiari.ttf'),
      font_size=10,
      x=4,
      y=115,
      scaling_factor=self.scaling_factor
    )

    text_images = [textbox, character_name]

    return location_images, talking_images, text_images

  def animate_action(
    self,
    cue: CharacterCue,
    action: Action,
    current_frame: int,
    location_images
  ):
    animations = []
    sfx = []
    if action.shake_effect:
      for location_image in location_images:
        location_image.shake_effect = True

    if action.asset_name is not None:
      effect_image = animation_cache.get_anim_img(
        os.path.join(self.assets_folder, action.asset_name),
        shake_effect=True,
        scaling_factor=self.scaling_factor
      )
      animations.append(
        SceneAnimation(
          location_images + [effect_image],
          length=action.length,
          start_frame=current_frame
        )
      )

    animations.append(
      SceneAnimation(
        location_images,
        length=action.length,
        start_frame=current_frame
      )
    )
    current_frame += self.lag_frames
    if action.sound_effect is not None:
      sfx.append(
        CharacterSoundEffect(
          sound_effect=action.sound_effect,
          character=cue.character
        )
      )

    if action.shake_effect:
      # Remove shake effect from all location images
      for location_image in location_images:
        location_image.shake_effect = False

    # silence action
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

    return animations, sfx, current_frame

  def animate_beat(
    self,
    cue: CharacterCue,
    beat: CharacterBeat,
    current_frame: int,
    location_images,
    talking_images,
    text_images
  ):
    animations = []
    sfx = []
    text_lines = split_str_into_newlines(
      beat.text,
      self.text_box_max_line_count
    )
    colour = None

    text = animation_cache.get_anim_text(
      text_lines,
      font_path=f"{self.assets_folder}/igiari/Igiari.ttf",
      font_size=15,
      x=5,
      y=130,
      typewriter_effect=True,
      colour=colour,
      scaling_factor=self.scaling_factor
    )
    num_frames = len(text_lines) + self.lag_frames

    # if obj["action"] == Action.TEXT_SHAKE_EFFECT:
    #   bg.shake_effect = True
    #   character.shake_effect = True
    #
    #   if bench is not None:
    #     bench.shake_effect = True
    #
    #   textbox.shake_effect = True

    animations.append(
      SceneAnimation(
        talking_images + text_images + [text],
        length=len(text_lines) - 1,
        start_frame=current_frame
      )
    )
    sfx.append(
      SoundEffect(
        type='bip',
        length=len(text_lines) - 1
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
    animations.append(
      SceneAnimation(
        location_images + text_images + [text, self.arrow],
        length=self.lag_frames,
        start_frame=len(text_lines) - 1
      )
    )

    current_frame += num_frames
    sfx.append(
      SoundEffect(
        type='silence',
        length=self.lag_frames
      )
    )
    return animations, sfx, current_frame

  class Character(IntEnum):
    PHOENIX = 1
    EDGEWORTH = 2
    GODOT = 3
    FRANZISKA = 4
    JUDGE = 5
    LARRY = 6
    MAYA = 7
    KARMA = 8
    PAYNE = 9
    MAGGEY = 10
    PEARL = 11
    LOTTA = 12
    GUMSHOE = 13
    GROSSBERG = 14

    def __str__(self):
      return str(self.name).capitalize()


def split_str_into_newlines(text: str, max_line_count):
  lines = []
  for line in wrap(text, max_line_count):
    lines.append(line + ' ')
  new_text = '\n'.join(lines)
  return new_text
