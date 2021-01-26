
from tqdm import tqdm

from comments import Comment


def load_script(data_path, characters, max_length):
  c_map = {c.name: c for c in characters}
  comments = []
  current_line = []
  previous_character = None

  with open(data_path) as f:
    lines = list(f)
    for line in tqdm(lines, desc='reading script'):
      if line.startswith('    ' * 9):
        current_character = c_map[line.strip().lower().capitalize()]

        if previous_character is not None and previous_character != current_character:
          text = ' '.join(current_line)
          comment = Comment(
            body=text,
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

  return comments
