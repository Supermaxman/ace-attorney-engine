
import os
from tqdm import tqdm
import torch
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM

import engine
from settings import Settings


class Comment(object):
  def __init__(self, body, author, emotion=None, score=0.0):
    self.body = body
    self.author = author
    self.emotion = emotion
    self.score = score


class Author(object):
  def __init__(self, name, character):
    self.name = name
    self.character = character


if __name__ == '__main__':
  data_path = Settings.DATA_PATH
  model_name = Settings.MODEL_NAME
  os.environ["PATH"] += Settings.FFMPEG_PATH
  max_length = None
  emotion_threshold = 0.5
  output_filename = Settings.OUTPUT_FILENAME

  tokenizer = AutoTokenizer.from_pretrained(model_name)
  model = AutoModelForSeq2SeqLM.from_pretrained(model_name)

  norm = torch.nn.Softmax(dim=-1)

  def get_emotion(text):
    input_ids = tokenizer.encode(
      text + '</s>',
      return_tensors='pt'
    )

    output = model.generate(
      input_ids=input_ids,
      max_length=2,
      output_scores=True,
      return_dict_in_generate=True
    )
    dec = [tokenizer.decode(ids) for ids in output.sequences]
    scores = norm(output.scores[0])
    score = float(scores.max(dim=-1)[0][0])
    label = dec[0].replace('<pad>', '').strip()
    return label, score

  characters = [
    Author(
      name='Randolph',
      character=engine.Character.JUDGE
    ),
    Author(
      name='Kaffee',
      character=engine.Character.PHOENIX
    ),
    Author(
      name='Jessep',
      character=engine.Character.GUMSHOE
    ),
    Author(
      name='Ross',
      character=engine.Character.EDGEWORTH
    ),
  ]

  c_map = {c.name: c for c in characters}
  comments = []
  current_line = []
  current_character = None
  previous_character = None
  with open(data_path) as f:
    lines = list(f)
    for line in tqdm(lines, desc='reading script...'):
      if line.startswith('    ' * 9):
        current_character = c_map[line.strip().lower().capitalize()]
        if previous_character is not None and previous_character != current_character:
          t = ' '.join(current_line)
          emotion, score = get_emotion(t)
          comment = Comment(
            body=t,
            emotion=emotion,
            score=score,
            author=previous_character
          )
          comments.append(comment)
          if max_length is not None and len(comments) >= max_length:
            break
          current_line.clear()
        previous_character = current_character
      elif line.startswith('    ' * 7):
        pass
      elif line.startswith('    ' * 6):
        line = line.strip()
        if line != '':
          current_line.append(line)

  # print()
  # for idx, comment in enumerate(comments):
  #   emotion = comment.emotion if comment.score > 0.5 else 'normal'
  #   print(f'{idx+1} {comment.score:.2f}: {emotion}')
  engine.comments_to_scene(
      comments,
      emotion_threshold=emotion_threshold,
      output_filename=output_filename,
      assets_folder=Settings.ASSETS_FOLDER
  )
