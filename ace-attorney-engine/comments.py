

class Comment(object):
  def __init__(self, body, author):
    self.body = body
    self.author = author


class EmotionComment(object):
  def __init__(self, body, author, emotion=None, score=0.0):
    self.body = body
    self.author = author
    self.emotion = emotion
    self.score = score


class Author(object):
  def __init__(self, name, character):
    self.name = name
    self.character = character
