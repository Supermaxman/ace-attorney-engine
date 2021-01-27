
from typing import List, Dict


class Scene(object):
  def __init__(self, characters=None):
    if characters is None:
      characters = []
    self.characters = characters
