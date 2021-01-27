

class Comment:
  def __init__(self, body, author):
    self.body = body
    self.author = author


class EmotionComment:
  def __init__(self, body, author, emotion=None, score=0.0):
    self.body = body
    self.author = author
    self.emotion = emotion
    self.score = score


class Author:
  def __init__(self, name, character):
    self.name = name
    self.character = character
