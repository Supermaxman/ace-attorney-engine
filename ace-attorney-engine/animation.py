
import random

from PIL import Image, ImageDraw, ImageFont
from typing import List, Dict


class AnimationCache:
  def __init__(self):
    # self._cache = {}
    self._img_cache = {}
    # self._text_cache = {}
    self._font_cache = {}

  def clear(self):
    self._img_cache.clear()
    self._font_cache.clear()

  def get_font(self, font_path, font_size, scaling_factor):
    key = hash(
      (font_path, font_size, scaling_factor)
    )

    if key not in self._font_cache:
      f = ImageFont.truetype(
        font_path,
        int(scaling_factor * font_size)
      )
      self._font_cache[key] = f
    else:
      f = self._font_cache[key]

    return f

  def get_anim_text(
    self, text, x=0, y=0, font_path=None, font_size=12, typewriter_effect=False, colour="#ffffff",
    scaling_factor=1.0
  ):
    if font_path is not None:
      font = self.get_font(font_path, font_size, scaling_factor)
    else:
      font = None

    a = AnimationText(
      text=text,
      font=font,
      x=int(scaling_factor*x),
      y=int(scaling_factor*y),
      typewriter_effect=typewriter_effect,
      colour=colour
    )
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
    scaling_factor: int = 1.0,
  ):
    img = self.get_image(path)
    a = AnimationImage(
      path,
      img,
      x=x, y=y, w=w, h=h,
      key_x=key_x, key_x_reverse=key_x_reverse,
      shake_effect=shake_effect,
      half_speed=half_speed,
      repeat=repeat,
      scaling_factor=scaling_factor
    )

    return a


animation_cache = AnimationCache()


class AnimationImage:
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
    scaling_factor: int = 1.0,
  ):
    self.scaling_factor = scaling_factor
    self.x = int(self.scaling_factor * x)
    self.y = int(self.scaling_factor * y)
    self.path = path
    self.key_x = key_x
    self.key_x_reverse = key_x_reverse
    img = img

    if img.format == "GIF" and img.is_animated:
      self.frames = []
      for idx in range(img.n_frames):
        img.seek(idx)
        w = img.size[0]
        h = img.size[1]
        self.frames.append(self.resize(img, w=w, h=h).convert("RGBA"))
    elif key_x is not None:
      if w is None and h is None:
        w = img.size[0]
        h = img.size[1]

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
      if w is None and h is None:
        # frame = img.convert("RGBA")
        w = img.size[0]
        h = img.size[1]
      self.frames = [self.resize(img, w=w, h=h).convert("RGBA")]

    self.w = self.frames[0].size[0]
    self.h = self.frames[0].size[1]
    self.shake_effect = shake_effect
    self.half_speed = half_speed
    self.repeat = repeat

  def resize(self, frame, *, w: int = None, h: int = None):
    if w is not None and h is not None:
      return frame.resize((int(self.scaling_factor * w), int(self.scaling_factor * h)))
    else:
      if w is not None:
        w_perc = w / float(frame.size[0])
        _h = int((float(frame.size[1]) * float(w_perc)))
        return frame.resize((int(self.scaling_factor * w), int(self.scaling_factor * _h)), Image.ANTIALIAS)
      if h is not None:
        h_perc = h / float(frame.size[1])
        _w = int((float(frame.size[0]) * float(h_perc)))
        return frame.resize((int(self.scaling_factor * _w), int(self.scaling_factor * h)), Image.ANTIALIAS)

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
      offset = (self.x + random.randint(-1, 1), self.y + random.randint(-1, 1))

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
        self.repeat, self.scaling_factor
      )
    )


class AnimationText:
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

    # TODO play with fonts to get cripser
    # fill = None,
    # font = None,
    # anchor = None,
    # spacing = 4,
    # align = "left",
    # direction = None,
    # features = None,
    # language = None,
    # stroke_width = 0,
    # stroke_fill = None,

    if self.font is not None:
      draw.text(
        (self.x, self.y),
        _text,
        font=self.font,
        fill=self.colour,
        spacing=4,
        stroke_width=0,
        stroke_fill=0
      )
    else:
      draw.text(
        (self.x, self.y),
        _text,
        fill=self.colour,
        spacing=4,
        stroke_width=0,
        stroke_fill=0
      )

    return background

  def __str__(self):
    return self.text


class SceneAnimation:
  def __init__(self, arr: List, length: int, start_frame: int = 0):
    self.frames = []
    text_idx = 0
    arr = list(
      filter(lambda x: x is not None, arr)
    )
    #     print([str(x) for x in arr])

    for idx in range(start_frame, start_frame + length):
      if isinstance(arr[0], AnimationImage):
        background = arr[0].render()
      else:
        background = arr[0]

      for obj in arr[1:]:
        if isinstance(obj, AnimationText):
          obj.render(background, frame=text_idx)
        else:
          obj.render(background, frame=idx)

      self.frames.append(background)
      text_idx += 1


def add_margin(pil_img, top, right, bottom, left):
  width, height = pil_img.size
  new_width = width + right + left
  new_height = height + top + bottom
  result = Image.new(pil_img.mode, (new_width, new_height), (0, 0, 0, 0))
  result.paste(pil_img, (left, top))

  return result
