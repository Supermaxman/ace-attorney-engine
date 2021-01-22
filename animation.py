from PIL import Image, ImageDraw, ImageFont
import numpy as np
import cv2
from typing import List, Dict
import os
import random as r
import random


class AnimCache:
  def __init__(self):
    self._cache = {}
    self._img_cache = {}
    self._text_cache = {}
    self._font_cache = {}

  def get_font(self, font_path, font_size):
    key = hash(
      (font_path, font_size)
    )
    if key not in self._font_cache:
      f = ImageFont.truetype(font_path, font_size)
      self._font_cache[key] = f
    else:
      f = self._font_cache[key]
    return f

  def get_anim_text(self, text, x=0, y=0, font_path=None, font_size=12, typewriter_effect=False, colour="#ffffff"):
    key = hash(
      (
        text, x, y, font_path, font_size, typewriter_effect, colour
      )
    )
    if key not in self._text_cache:
      if font_path is not None:
        font = self.get_font(font_path, font_size)
      else:
        font = None
      a = AnimText(
        text=text,
        font=font,
        x=x,
        y=y,
        typewriter_effect=typewriter_effect,
        colour=colour
      )
      self._text_cache[key] = a
    else:
      a = self._text_cache[key]
    return a

  def get_image(self, path):
    if path in self._img_cache:
      img = self._img_cache[path]
    else:
      img = Image.open(path, "r")
      self._img_cache[path] = img
    return img

  def get_anim_img(
    self,
    path: str,
    *,
    x: int = 0,
    y: int = 0,
    w: int = None,
    h: int = None,
    key_x: int = None,
    key_x_reverse: bool = True,
    shake_effect: bool = False,
    half_speed: bool = False,
    repeat: bool = True,
  ):
    key = hash(
      (
        path, x, y, w, h,
        key_x,
        key_x_reverse,
        shake_effect,
        half_speed,
        repeat
      )
    )
    if key not in self._cache:
      img = self.get_image(path)
      a = AnimImg(
        path,
        img,
        x=x, y=y, w=w, h=h,
        key_x=key_x, key_x_reverse=key_x_reverse,
        shake_effect=shake_effect,
        half_speed=half_speed,
        repeat=repeat
      )
      self._cache[key] = a
    else:
      a = self._cache[key]
    return a


anim_cache = AnimCache()


class AnimImg:
  def __init__(
    self,
    path: str,
    img: Image,
    *,
    x: int = 0,
    y: int = 0,
    w: int = None,
    h: int = None,
    key_x: int = None,
    key_x_reverse: bool = True,
    shake_effect: bool = False,
    half_speed: bool = False,
    repeat: bool = True,
  ):
    self.x = x
    self.y = y
    self.path = path
    self.key_x = key_x
    self.key_x_reverse = key_x_reverse
    img = img
    if img.format == "GIF" and img.is_animated:
      self.frames = []
      for idx in range(img.n_frames):
        img.seek(idx)
        self.frames.append(self.resize(img, w=w, h=h).convert("RGBA"))
    elif key_x is not None:
      self.frames = []
      for x_pad in range(key_x):
        self.frames.append(
          add_margin(
            self.resize(img, w=w, h=h).convert("RGBA"), 0, 0, 0, x_pad
          )
        )
      if key_x_reverse:
        for x_pad in reversed(range(key_x)):
          self.frames.append(
            add_margin(
              self.resize(img, w=w, h=h).convert("RGBA"), 0, 0, 0, x_pad
            )
          )
    else:
      self.frames = [self.resize(img, w=w, h=h).convert("RGBA")]
    self.w = self.frames[0].size[0]
    self.h = self.frames[0].size[1]
    self.shake_effect = shake_effect
    self.half_speed = half_speed
    self.repeat = repeat

  def resize(self, frame, *, w: int = None, h: int = None):
    if w is not None and h is not None:
      return frame.resize((w, h))
    else:
      if w is not None:
        w_perc = w / float(frame.size[0])
        _h = int((float(frame.size[1]) * float(w_perc)))
        return frame.resize((w, _h), Image.ANTIALIAS)
      if h is not None:
        h_perc = h / float(frame.size[1])
        _w = int((float(frame.size[0]) * float(h_perc)))
        return frame.resize((_w, h), Image.ANTIALIAS)
    return frame

  def render(self, background: Image = None, frame: int = 0):
    if frame > len(self.frames) - 1:
      if self.repeat:
        frame = frame % len(self.frames)
      else:
        frame = len(self.frames) - 1
    if self.half_speed and self.repeat:
      frame = int(frame / 2)
    _img = self.frames[frame]
    if background is None:
      _w, _h = _img.size
      _background = Image.new("RGBA", (_w, _h), (255, 255, 255, 255))
    else:
      _background = background
    bg_w, bg_h = _background.size
    offset = (self.x, self.y)
    if self.shake_effect:
      offset = (self.x + r.randint(-1, 1), self.y + r.randint(-1, 1))
    _background.paste(_img, offset, mask=_img)
    if background is None:
      return _background

  def __str__(self):
    return self.path

  def __eq__(self, other):
    return hash(self) == hash(other)

  def __hash__(self):
    return hash(
      (
        self.path, self.x, self.y, self.w, self.h,
        self.key_x,
        self.key_x_reverse,
        self.shake_effect,
        self.half_speed,
        self.repeat
      )
    )


class AnimText:
  def __init__(
    self,
    text: str,
    *,
    x: int = 0,
    y: int = 0,
    font=None,
    typewriter_effect: bool = False,
    colour: str = "#ffffff",
  ):
    self.x = x
    self.y = y
    self.text = text
    self.typewriter_effect = typewriter_effect
    self.font = font
    self.colour = colour

  def render(self, background: Image, frame: int = 0):
    draw = ImageDraw.Draw(background)
    _text = self.text
    if self.typewriter_effect:
      _text = _text[:frame]
    if self.font is not None:
      draw.text((self.x, self.y), _text, font=self.font, fill=self.colour)
    else:
      draw.text((self.x, self.y), _text, fill=self.colour)
    return background

  def __str__(self):
    return self.text


class AnimScene:
  def __init__(self, arr: List, length: int, start_frame: int = 0):
    self.frames = []
    text_idx = 0
    arr = list(
      filter(lambda x: x is not None, arr)
    )
    #     print([str(x) for x in arr])
    for idx in range(start_frame, length + start_frame):
      if isinstance(arr[0], AnimImg):
        background = arr[0].render()
      else:
        background = arr[0]
      for obj in arr[1:]:
        if isinstance(obj, AnimText):
          obj.render(background, frame=text_idx)
        else:
          obj.render(background, frame=idx)
      self.frames.append(background)
      text_idx += 1


class AnimVideo:
  def __init__(self, scenes: List[AnimScene], fps: int = 10, extension='mp4', codec=None):
    self.scenes = scenes
    self.fps = fps
    if codec is None:
      codec = cv2.VideoWriter_fourcc(*'MPEG')
    self.codec = codec
    self.extension = extension

  def render(self, output_path: str = None):
    if output_path is None:
      if not os.path.exists("tmp"):
        os.makedirs("tmp")
      rnd_hash = random.getrandbits(64)
      output_path = f"tmp/{rnd_hash}.{self.extension}"
    background = self.scenes[0].frames[0]
    if os.path.isfile(output_path):
      os.remove(output_path)
    video = cv2.VideoWriter(output_path, self.codec, self.fps, background.size)
    for scene in self.scenes:
      for frame in scene.frames:
        video.write(cv2.cvtColor(np.array(frame), cv2.COLOR_RGB2BGR))
    video.release()
    return output_path


def add_margin(pil_img, top, right, bottom, left):
  width, height = pil_img.size
  new_width = width + right + left
  new_height = height + top + bottom
  result = Image.new(pil_img.mode, (new_width, new_height), (0, 0, 0, 0))
  result.paste(pil_img, (left, top))
  return result
