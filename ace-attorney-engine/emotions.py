from typing import List, Tuple

from tqdm import tqdm
import torch
from torch.utils.data import DataLoader, Dataset
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM

from comments import Comment, EmotionComment


class EmotionModel(object):
  def __init__(self, model_name, batch_size=8, max_seq_len=512, num_workers=4, force_max_seq_len=False):
    self.model_name = model_name
    self.tokenizer = AutoTokenizer.from_pretrained(model_name)
    self.model = AutoModelForSeq2SeqLM.from_pretrained(model_name)
    self.model.eval()
    self.norm = torch.nn.Softmax(dim=-1)
    self.batch_size = batch_size
    self.max_seq_len = max_seq_len
    self.force_max_seq_len = force_max_seq_len
    self.num_workers = num_workers
    self.collator = BatchCollator(
      self.tokenizer,
      max_seq_len=self.max_seq_len,
      force_max_seq_len=self.force_max_seq_len
    )

  def detect_emotions(self, comments: List[Comment]) -> List[EmotionComment]:
    texts = [c.body for c in comments]
    emotions, scores = self._get_emotions(texts)
    emotion_comments = []
    for comment, emotion, score in zip(comments, emotions, scores):
      emotion_comment = EmotionComment(
        body=comment.body,
        emotion=emotion,
        score=score,
        author=comment.author
      )
      emotion_comments.append(emotion_comment)
    return emotion_comments

  def _get_emotions(self, texts: List[str]) -> Tuple[List[str], List[float]]:
    dataset = CommentDataset(texts)
    data_loader = DataLoader(
      dataset,
      batch_size=self.batch_size,
      shuffle=False,
      num_workers=self.num_workers,
      collate_fn=self.collator,
      drop_last=False
    )
    emotions = []
    scores = []
    with torch.no_grad():
      for batch in tqdm(data_loader, total=len(data_loader), desc='running emotion detection...'):
        output = self.model.generate(
          input_ids=batch['input_ids'],
          attention_mask=batch['attention_mask'],
          max_length=2,
          output_scores=True,
          return_dict_in_generate=True
        )
        # [bsize]
        b_emotions = self.tokenizer.batch_decode(output.sequences[:, -1:], skip_special_tokens=True)
        # [bsize]
        b_scores = self.norm(output.scores[0]).max(dim=-1)[0].tolist()
        b_scores = [float(score) for score in b_scores]
        emotions.extend(b_emotions)
        scores.extend(b_scores)
    return emotions, scores


class BatchCollator(object):
  def __init__(self, tokenizer, max_seq_len: int, force_max_seq_len: bool):
    super().__init__()
    self.tokenizer = tokenizer
    self.max_seq_len = max_seq_len
    self.force_max_seq_len = force_max_seq_len

  def __call__(self, examples):
    # creates text examples
    texts = []
    for text in examples:
      texts.append(text + '</s>')
    # "input_ids": batch["input_ids"].to(device),
    # "attention_mask": batch["attention_mask"].to(device),
    tokenizer_batch = self.tokenizer.batch_encode_plus(
      batch_text_or_text_pairs=texts,
      add_special_tokens=True,
      padding='max_length' if self.force_max_seq_len else 'longest',
      return_tensors='pt',
      truncation=True,
      max_length=self.max_seq_len
    )
    batch = {
      'input_ids': tokenizer_batch['input_ids'],
      'attention_mask': tokenizer_batch['attention_mask'],
    }

    return batch


class CommentDataset(Dataset):
  def __init__(self, examples):
    self.examples = examples

  def __len__(self):
    return len(self.examples)

  def __getitem__(self, idx):
    if torch.is_tensor(idx):
      idx = idx.tolist()

    ex = self.examples[idx]

    return ex
