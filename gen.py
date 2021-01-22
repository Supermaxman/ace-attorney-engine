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
  # settings
  asset_folder        = Settings.ASSETS_FOLDER
  data_path           = Settings.DATA_PATH
  os.environ["PATH"] += Settings.FFMPEG_PATH
  model_name          = Settings.MODEL_NAME
  output_filename     = Settings.OUTPUT_FILENAME
  max_comments = 30

  tokenizer = AutoTokenizer.from_pretrained(model_name)
  model = AutoModelForSeq2SeqLM.from_pretrained(model_name)
  norm = torch.nn.Softmax(dim=-1)

  # TODO: move this out of the main section
  # TODO: don't be lazy and use the defined variables, pass them instead
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
      name='Holt',
      character=engine.Character.JUDGE
    ),
    Author(
      name='Clinton',
      character=engine.Character.PHOENIX
    ),
    Author(
      name='Trump',
      character=engine.Character.EDGEWORTH
    ),
  ]

  c_map = {c.name: c for c in characters}
  comments = []
  current_c_name = None
  with open(data_path, errors='ignore') as f:
    lines = list(f)
    for line in tqdm(lines):
      line = line.strip()
      if not line or line.startswith('('):
        continue
      line = line.replace('[Interruption]', '')
      line = line.split(':')
      c_name = line[0].strip().lower().capitalize()
      if c_name in c_map:
        current_c_name = c_name
        t = ':'.join(line[1:])
      else:
        t = ':'.join(line)
      emotion, score = get_emotion(t)
      comment = Comment(
        body=t,
        emotion=emotion,
        score=score,
        author=c_map[current_c_name]
      )
      comments.append(comment)
      if max_comments is not None and len(comments) >= max_comments:
        break

  for comment in comments:
    print(f'{comment.author.name}: ({comment.emotion}|{comment.score}) {comment.body}')

  engine.comments_to_scene(
      comments,
      output_filename=output_filename,
      assets_folder=asset_folder,
      emotion_threshold=0.5
  )
