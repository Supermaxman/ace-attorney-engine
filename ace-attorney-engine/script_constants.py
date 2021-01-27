
from enum import IntEnum


class Location(IntEnum):
  COURTROOM_LEFT = 1
  WITNESS_STAND = 2
  COURTROOM_RIGHT = 3
  CO_COUNCIL = 4
  JUDGE_STAND = 5
  COURT_HOUSE = 6


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


class Action(IntEnum):
  TEXT = 1
  SHAKE_EFFECT = 2
  OBJECTION = 3
  TEXT_SHAKE_EFFECT = 4
  HOLD_IT = 5


location_map = {
  Location.COURTROOM_LEFT: "defenseempty.png",
  Location.WITNESS_STAND: "witnessempty.png",
  Location.COURTROOM_RIGHT: "prosecutorempty.png",
  Location.CO_COUNCIL: "helperstand.png",
  Location.JUDGE_STAND: "judgestand.png",
  Location.COURT_HOUSE: "courtroomoverview.png",
}

character_map = {
  Character.PHOENIX: "Sprites-phoenix",
  Character.EDGEWORTH: "Sprites-edgeworth",
  Character.GODOT: "Sprites-Godot",
  Character.FRANZISKA: "Sprites-franziska",
  Character.JUDGE: "Sprites-judge",
  Character.LARRY: "Sprites-larry",
  Character.MAYA: "Sprites-maya",
  Character.KARMA: "Sprites-karma",
  Character.PAYNE: "Sprites-payne",
  Character.MAGGEY: "Sprites-Maggey",
  Character.PEARL: "Sprites-Pearl",
  Character.LOTTA: "Sprites-lotta",
  Character.GUMSHOE: "Sprites-gumshoe",
  Character.GROSSBERG: "Sprites-grossberg",
}


character_location_map = {
  Character.PHOENIX: Location.COURTROOM_LEFT,
  Character.EDGEWORTH: Location.COURTROOM_RIGHT,
  Character.GODOT: Location.COURTROOM_RIGHT,
  Character.FRANZISKA: Location.COURTROOM_RIGHT,
  Character.JUDGE: Location.JUDGE_STAND,
  Character.LARRY: Location.WITNESS_STAND,
  Character.MAYA: Location.CO_COUNCIL,
  Character.KARMA: Location.COURTROOM_RIGHT,
  Character.PAYNE: Location.COURTROOM_RIGHT,
  Character.MAGGEY: Location.WITNESS_STAND,
  Character.PEARL: Location.WITNESS_STAND,
  Character.LOTTA: Location.WITNESS_STAND,
  Character.GUMSHOE: Location.WITNESS_STAND,
  Character.GROSSBERG: Location.WITNESS_STAND,
}

# sadness
# joy
# love
# anger
# fear
# surprise
objection_emotions = {
  'anger'
}

shake_emotions = {
  'joy'
}

hold_it_emotions = {
  'surprise'
}

character_emotions = {
  # "happy": ["confident", "pointing", "smirk"],
  # "neutral": ["document", "normal", "thinking"],
  # "sad": ["emo", "handondesk"],
  Character.EDGEWORTH: {
    "sadness": ["emo"],
    "joy": ["confident", "pointing"],
    "love": ["smirk"],
    "anger": ["handondesk"],
    "fear": ["emo"],
    "surprise": ["handondesk"],
    "normal": ["document", "normal", "thinking"]
  },
  # "happy": ["confident", "pointing", "handsondesk"],
  # "neutral": ["document", "normal", "thinking", "coffee"],
  # "sad": ["emo", "sheepish", "sweating"],
  Character.PHOENIX: {
    "sadness": ["emo"],
    "joy": ["confident", "pointing"],
    "love": ["confident", "pointing"],
    "anger": ["handsondesk"],
    "fear": ["emo", "sweating", "sheepish"],
    "surprise": ["handsondesk"],
    "normal": ["document", "normal", "thinking", "coffee"]
  },
  # "happy": ["bench"],
  # "neutral": ["bench-hum", "bench-profile"],
  # "sad": ["bench-strict", "bench-ugh"],
  Character.MAYA: {
    "sadness": ["bench-strict", "bench-ugh"],
    "joy": ["bench-hum"],
    "love": ["bench"],
    "anger": ["bench-strict"],
    "fear": ["bench-ugh"],
    "surprise": ["bench-hum"],
    "normal": ["bench-profile"],
  },
  # "happy": ["hello"],
  # "neutral": ["normal"],
  # "sad": ["extra", "mad", "nervous"],
  Character.LARRY: {
    "sadness": ["extra"],
    "joy": ["hello"],
    "love": ["hello"],
    "anger": ["mad"],
    "fear": ["nervous"],
    "surprise": ["nervous"],
    "normal": ["normal"],
  },
  # "happy": ["normal"],
  # "neutral": ["normal"],
  # "sad": ["steams", "pointing"],
  Character.GODOT: {
    "sadness": ["steams"],
    "joy": ["normal"],
    "love": ["normal"],
    "anger": ["pointing"],
    "fear": ["steams"],
    "surprise": ["steams"],
    "normal": ["normal"],
  },
  # "happy": ["ha"],
  # "neutral": ["ready"],
  # "sad": ["mad", "sweating", "withwhip"],
  Character.FRANZISKA: {
    "sadness": ["sweating"],
    "joy": ["ha"],
    "love": ["ha"],
    "anger": ["mad"],
    "fear": ["sweating"],
    "surprise": ["withwhip"],
    "normal": ["ready"],
  },
  # "happy": ["nodding"],
  # "neutral": ["normal"],
  # "sad": ["headshake", "warning"],
  Character.JUDGE: {
    "sadness": ["headshake"],
    "joy": ["normal"],
    "love": ["nodding"],
    "anger": ["warning"],
    "fear": ["warning"],
    "surprise": ["warning"],
    "normal": ["normal"],
  },
  # "happy": ["smirk", "snap"],
  # "neutral": ["normal"],
  # "sad": ["badmood", "break", "sweat"],
  Character.KARMA: {
    "sadness": ["badmood"],
    "joy": ["normal"],
    "love": ["smirk", "snap"],
    "anger": ["break"],
    "fear": ["sweat"],
    "surprise": ["break"],
    "normal": ["normal"],
  },
  # "happy": ["confident"],
  # "neutral": ["normal"],
  # "sad": ["sweating"],
  Character.PAYNE: {
    "sadness": ["sweating"],
    "joy": ["normal"],
    "love": ["confident"],
    "anger": ["sweating"],
    "fear": ["sweating"],
    "surprise": ["sweating"],
    "normal": ["normal"],
  },
  # "happy": ["pumped", "shining"],
  # "neutral": ["normal"],
  # "sad": ["sad"],
  Character.MAGGEY: {
    "sadness": ["sad"],
    "joy": ["pumped"],
    "love": ["shining"],
    "anger": ["sad"],
    "fear": ["sad"],
    "surprise": ["sad"],
    "normal": ["normal"],
  },
  # "happy": ["sparkle", "surprised"],
  # "neutral": ["normal", "shy", "thinking"],
  # "sad": ["cries", "disappointed", "fight"],
  Character.PEARL: {
    "sadness": ["cries"],
    "joy": ["sparkle"],
    "love": ["sparkle"],
    "anger": ["fight", "disappointed"],
    "fear": ["cries"],
    "surprise": ["surprised"],
    "normal": ["normal", "thinking", "shy"],
  },
  # "happy": ["confident", "smiling"],
  # "neutral": ["normal", "shy", "thinking"],
  # "sad": ["badmood", "disappointed", "mad"],
  Character.LOTTA: {
    "sadness": ["badmood"],
    "joy": ["confident", "smiling"],
    "love": ["confident", "smiling"],
    "anger": ["mad", "disappointed"],
    "fear": ["badmood"],
    "surprise": ["mad"],
    "normal": ["normal", "shy", "thinking"],
  },
  # "happy": ["laughing", "confident", "pumped"],
  # "neutral": ["normal", "shy", "side", "thinking"],
  # "sad": ["disheartened", "mad"],
  Character.GUMSHOE: {
    "sadness": ["disheartened"],
    "joy": ["side"],
    "love": ["laughing", "confident", "pumped"],
    "anger": ["mad"],
    "fear": ["disheartened"],
    "surprise": ["disheartened"],
    "normal": ["normal", "side", "thinking"],
  },
  # "happy": ["normal"],
  # "neutral": ["normal"],
  # "sad": ["sweating"],
  Character.GROSSBERG: {
    "sadness": ["sweating"],
    "joy": ["normal"],
    "love": ["normal"],
    "anger": ["sweating"],
    "fear": ["sweating"],
    "surprise": ["sweating"],
    "normal": ["normal"],
  },
}

audio_emotions = {
  "normal": "03 - Turnabout Courtroom - Trial",
  "objection": "08 - Pressing Pursuit _ Cornered",
  "holdit": "11 - Pressing Pursuit _ Cornered , Variation",
  "sadness": "10 - Suspense",
  "joy": "03 - Turnabout Courtroom - Trial",
  "love": "05 - Logic and Trick",
  "anger": "11 - Pressing Pursuit _ Cornered , Variation",
  "fear": "10 - Suspense",
  "surprise": "05 - Logic and Trick",
}
