"""Talon code for dictating text. Common to both command and dicatation modes."""
# Disable linter warnings caused by Talon conventions.
# pylint: disable=no-self-argument, no-method-argument, relative-beyond-top-level
# pyright: reportSelfClsParameterName=false, reportGeneralTypeIssues=false
# mypy: ignore-errors

from talon import Context, Module, actions, grammar
from .lib import format_util
from .user_settings import load_dict_from_csv

mod = Module()
ctx = Context()

mod.list("vocabulary", desc="Additional vocabulary words")
mod.list("person_name", desc="Names of people")
mod.list("unicode", desc="Named Unicode strings, such as emoji")

# "dictate.word_map" is used by `actions.dictate.replace_words` to rewrite words Talon recognized.
# Entries in word_map don't change the priority with which Talon recognizes some words over others.
ctx.settings["dictate.word_map"] = load_dict_from_csv("words_to_replace.csv")

# "user.vocabulary" is used to explicitly add words/phrases that Talon doesn't recognize. Words in
# user.vocabulary (or other lists and captures) are "command-like" and their recognition is
# prioritized over ordinary words.
ctx.lists["user.vocabulary"] = load_dict_from_csv("additional_words.csv")

# Names of people.
ctx.lists["user.person_name"] = load_dict_from_csv("names.csv")

# Named Unicode strings (e.g. emoji).
ctx.lists["user.unicode"] = load_dict_from_csv("unicode.csv")


def _capture_to_words(m):
  words = []
  for item in m:
    if isinstance(item, grammar.vm.Phrase):
      words.extend(actions.dictate.replace_words(actions.dictate.parse_words(item)))
    else:
      words.extend(item.split(" "))
  return words


def _format_captured_text(m):
  words = _capture_to_words(m)
  result = ""
  for i, curr_word in enumerate(words):
    if i > 0 and format_util.needs_space_between(words[i - 1], curr_word):
      result += " "
    result += curr_word
  return result


@mod.capture(rule="gene may {self.person_name}")  # "gene may" sounds like 人名.
def person_name(m) -> str:
  """A person's name."""
  return m.person_name


@mod.capture(rule="({user.vocabulary} | <word>)")
def word(m) -> str:
  """A single word, including user-defined vocabulary."""
  try:
    return m.vocabulary
  except AttributeError:
    return " ".join(actions.dictate.replace_words(actions.dictate.parse_words(m.word)))


@mod.capture(rule="({user.vocabulary} | <phrase>)+")
def text(m) -> str:
  """A sequence of words, including user-defined vocabulary."""
  return _format_captured_text(m)


@mod.capture(rule="({user.punctuation} | <user.dictate_letters> | <user.dictate_number> | " +
             "<user.dictate_abbreviation> | <user.file_extension> | <user.person_name> | " +
             "{user.vocabulary} | <phrase>)+")
def prose(m) -> str:
  """Prose that is auto-spaced and capitalized. Allows abbreviations, letters, numbers, file
  extensions, and punctuation."""
  capitalized = format_util.auto_capitalize(_format_captured_text(m))
  return capitalized


@mod.capture(
    rule="(<user.dictate_letters> | <user.dictate_number> | <user.dictate_abbreviation> | " +
    "{user.vocabulary} | <phrase>)+")
def formatter_text(m) -> str:
  """Text for formatters. Allows abbreviations, letters, and numbers."""
  return _format_captured_text(m)
