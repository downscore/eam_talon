"""Code for implementing Scrambler commands over matched and modified text ranges."""

from typing import Callable, Optional
from .format_util import FormatOptions, WordCapitalization, format_phrase, format_word_capitalization, guess_capitalization
from .scrambler_types import CommandType, EditorAction, EditorActionType, TextMatch, TextRange, UtilityFunctions
from .text_util import StrippedString


def _intersect_ranges(range1: TextRange, range2: TextRange) -> Optional[TextRange]:
  """Calculate the intersection of two ranges. Returns None if they do not intersect."""
  if range1.start > range2.end or range2.start > range1.end:
    return None
  return TextRange(max(range1.start, range2.start), min(range1.end, range2.end))


def _perform_command_select(text: str, selection_range: TextRange, match: TextMatch,
                            insert_text: str, lambda_func: Optional[Callable[[str], str]],
                            utility_functions: UtilityFunctions) -> list[EditorAction]:
  """Select the matched range."""
  del text, selection_range, insert_text, lambda_func, utility_functions
  return [EditorAction(EditorActionType.SET_SELECTION_RANGE, match.text_range)]


def _perform_command_clear_move_cursor(text: str,
                                       selection_range: TextRange,
                                       match: TextMatch,
                                       insert_text: str,
                                       lambda_func: Optional[Callable[[str], str]],
                                       utility_functions: UtilityFunctions,
                                       use_deletion_range: bool = False) -> list[EditorAction]:
  """Clear the matched text and move the cursor where it was. Note: Unlike the clear command that it
  does not move the cursor, this function does not use the deletion range by default."""
  del text, selection_range, insert_text, utility_functions, lambda_func
  deletion_range = (match.deletion_range if use_deletion_range and match.deletion_range is not None
                    else match.text_range)
  return [EditorAction(EditorActionType.DELETE_RANGE, deletion_range)]


def _perform_command_clear_no_move(text: str,
                                   selection_range: TextRange,
                                   match: TextMatch,
                                   insert_text: str,
                                   lambda_func: Optional[Callable[[str], str]],
                                   utility_functions: UtilityFunctions,
                                   use_deletion_range: bool = True) -> list[EditorAction]:
  """Clear the matched text but preserve cursor position."""
  del text, insert_text, utility_functions, lambda_func
  deletion_range = (match.deletion_range if use_deletion_range and match.deletion_range is not None
                    else match.text_range)

  # Compute selected range after deletion.
  range_after = selection_range

  # If range to delete intersects selected range, we will move the cursor after the deletion.
  intersection = _intersect_ranges(selection_range, deletion_range)
  if intersection is not None:
    range_after = TextRange(deletion_range.end, deletion_range.end)

  # Adjust range if we are deleting text before the selection range.
  if deletion_range.start <= range_after.start:
    range_after = TextRange(range_after.start - deletion_range.length(),
                            range_after.end - deletion_range.length())

  return [
      EditorAction(EditorActionType.DELETE_RANGE, deletion_range),
      EditorAction(EditorActionType.SET_SELECTION_RANGE, range_after),
  ]


def _perform_command_move_cursor_before(text: str, selection_range: TextRange, match: TextMatch,
                                        insert_text: str, lambda_func: Optional[Callable[[str],
                                                                                         str]],
                                        utility_functions: UtilityFunctions) -> list[EditorAction]:
  """Move cursor before the matched range."""
  del text, selection_range, insert_text, utility_functions, lambda_func
  return [
      EditorAction(EditorActionType.SET_SELECTION_RANGE,
                   TextRange(match.text_range.start, match.text_range.start))
  ]


def _perform_command_move_cursor_after(text: str, selection_range: TextRange, match: TextMatch,
                                       insert_text: str, lambda_func: Optional[Callable[[str],
                                                                                        str]],
                                       utility_functions: UtilityFunctions) -> list[EditorAction]:
  """Move cursor after the matched range."""
  del text, selection_range, insert_text, utility_functions, lambda_func
  return [
      EditorAction(EditorActionType.SET_SELECTION_RANGE,
                   TextRange(match.text_range.end, match.text_range.end))
  ]


def _perform_command_cut_to_clipboard(text: str, selection_range: TextRange, match: TextMatch,
                                      insert_text: str, lambda_func: Optional[Callable[[str], str]],
                                      utility_functions: UtilityFunctions) -> list[EditorAction]:
  """Delete the matched text and copy it to the clipboard."""
  del insert_text
  result = _perform_command_clear_no_move(text, selection_range, match, "", lambda_func,
                                          utility_functions)
  result.append(
      EditorAction(EditorActionType.SET_CLIPBOARD_WITH_HISTORY,
                   text=match.text_range.extract(text)))
  return result


def _perform_command_copy_to_clipboard(text: str, selection_range: TextRange, match: TextMatch,
                                       insert_text: str, lambda_func: Optional[Callable[[str],
                                                                                        str]],
                                       utility_functions: UtilityFunctions) -> list[EditorAction]:
  """Copies the matched text to the clipboard without moving the cursor."""
  del selection_range, insert_text, utility_functions, lambda_func
  return [
      EditorAction(EditorActionType.SET_CLIPBOARD_WITH_HISTORY, text=match.text_range.extract(text))
  ]


def _perform_command_bring(text: str, selection_range: TextRange, match: TextMatch,
                           insert_text: str, lambda_func: Optional[Callable[[str], str]],
                           utility_functions: UtilityFunctions) -> list[EditorAction]:
  """Copies the matched text to the cursor position or the "to" match."""
  del selection_range, insert_text, utility_functions, lambda_func
  result: list[EditorAction] = []
  result.append(EditorAction(EditorActionType.INSERT_TEXT, text=match.text_range.extract(text)))
  return result


def _perform_command_replace(text: str, selection_range: TextRange, match: TextMatch,
                             insert_text: str, lambda_func: Optional[Callable[[str], str]],
                             utility_functions: UtilityFunctions) -> list[EditorAction]:
  """Replace the matched target with a given string."""
  del text, utility_functions, lambda_func

  # Compute selected range after replacement.
  range_after = selection_range

  # We only need to modify the range after if the replacement and original are different lengths.
  diff_chars = match.text_range.length() - len(insert_text)
  if diff_chars != 0:
    # If range to replace intersects selected range, we will move the cursor after the replacement.
    intersection = _intersect_ranges(selection_range, match.text_range)
    if intersection is not None:
      range_after = TextRange(match.text_range.end, match.text_range.end)

    # Adjust range if we are replacing text before the selection range.
    if match.text_range.start <= range_after.start:
      range_after = TextRange(range_after.start - diff_chars, range_after.end - diff_chars)

  return [
      EditorAction(EditorActionType.DELETE_RANGE, match.text_range),
      EditorAction(EditorActionType.INSERT_TEXT, text=insert_text),
      EditorAction(EditorActionType.SET_SELECTION_RANGE, range_after),
  ]


def _perform_command_replace_with_lambda(text: str, selection_range: TextRange, match: TextMatch,
                                         insert_text: str, lambda_func: Optional[Callable[[str],
                                                                                          str]],
                                         utility_functions: UtilityFunctions) -> list[EditorAction]:
  """Replace the matched string with lambda output."""
  del insert_text
  if lambda_func is None:
    raise ValueError("Lambda function required for replace with lambda command")
  processed = lambda_func(match.text_range.extract(text))
  return _perform_command_replace(text, selection_range, match, processed, lambda_func,
                                  utility_functions)


def _perform_command_replace_word_match_case(
    text: str, selection_range: TextRange, match: TextMatch, insert_text: str,
    lambda_func: Optional[Callable[[str], str]],
    utility_functions: UtilityFunctions) -> list[EditorAction]:
  """Replace a word and match its case."""
  # Guess casing of the word to replace and match it with the new word.
  stripped = StrippedString(match.text_range.extract(text))
  guessed_capitalization = guess_capitalization(stripped.stripped)
  replacement = format_word_capitalization(insert_text, guessed_capitalization)

  return _perform_command_replace(text, selection_range, match, replacement, lambda_func,
                                  utility_functions)


def _perform_command_next_homophone(text: str, selection_range: TextRange, match: TextMatch,
                                    insert_text: str, lambda_func: Optional[Callable[[str], str]],
                                    utility_functions: UtilityFunctions) -> list[EditorAction]:
  """Replace a word with its next homophone."""
  del insert_text
  # Strip the word to get homophones for, and retain padding info.
  stripped = StrippedString(match.text_range.extract(text))

  # Handle casing and replace non-ascii apostrophes with an ascii quote.
  guessed_capitalization = guess_capitalization(stripped.stripped)
  word_key = stripped.stripped.lower().replace("’", "'")

  # Get homophone for the word. No-op if there is no homophone.
  homophone_stripped = utility_functions.get_next_homophone(word_key)
  if not homophone_stripped:
    print(f"Scrambler: No homophone found. Word: {stripped.stripped}")
    return []

  # Match original case and whitespace padding.
  homophone = format_word_capitalization(homophone_stripped, guessed_capitalization)
  homophone = stripped.apply_padding(homophone)

  return _perform_command_replace(text, selection_range, match, homophone, lambda_func,
                                  utility_functions)


def _perform_command_title_case(text: str, selection_range: TextRange, match: TextMatch,
                                insert_text: str, lambda_func: Optional[Callable[[str], str]],
                                utility_functions: UtilityFunctions) -> list[EditorAction]:
  """Title case the matched target."""
  del insert_text
  # Always capitalize first word in case it is "a", "the", etc.
  options = FormatOptions(WordCapitalization.CAPITALIZE_FIRST_PRESERVE_FOLLOWING,
                          WordCapitalization.TITLE_CASE_PRESERVE_FOLLOWING)
  original = match.text_range.extract(text)
  formatted = format_phrase(original, options)
  return _perform_command_replace(text, selection_range, match, formatted, lambda_func,
                                  utility_functions)


def _perform_command_lowercase(text: str, selection_range: TextRange, match: TextMatch,
                               insert_text: str, lambda_func: Optional[Callable[[str], str]],
                               utility_functions: UtilityFunctions) -> list[EditorAction]:
  """Make the matched target lowercase."""
  del insert_text
  # Always capitalize first word in case it is "a", "the", etc.
  options = FormatOptions(WordCapitalization.LOWERCASE, WordCapitalization.LOWERCASE)
  original = match.text_range.extract(text)
  formatted = format_phrase(original, options)
  return _perform_command_replace(text, selection_range, match, formatted, lambda_func,
                                  utility_functions)


def _perform_command_uppercase(text: str, selection_range: TextRange, match: TextMatch,
                               insert_text: str, lambda_func: Optional[Callable[[str], str]],
                               utility_functions: UtilityFunctions) -> list[EditorAction]:
  """Make the matched target all uppercase."""
  del insert_text
  options = FormatOptions(WordCapitalization.UPPERCASE, WordCapitalization.UPPERCASE)
  original = match.text_range.extract(text)
  formatted = format_phrase(original, options)
  return _perform_command_replace(text, selection_range, match, formatted, lambda_func,
                                  utility_functions)


_COMMAND_FUNCTIONS = {
    CommandType.SELECT: _perform_command_select,
    CommandType.CLEAR_MOVE_CURSOR: _perform_command_clear_move_cursor,
    CommandType.CLEAR_NO_MOVE: _perform_command_clear_no_move,
    CommandType.MOVE_CURSOR_BEFORE: _perform_command_move_cursor_before,
    CommandType.MOVE_CURSOR_AFTER: _perform_command_move_cursor_after,
    CommandType.CUT_TO_CLIPBOARD: _perform_command_cut_to_clipboard,
    CommandType.COPY_TO_CLIPBOARD: _perform_command_copy_to_clipboard,
    CommandType.BRING: _perform_command_bring,
    CommandType.NEXT_HOMOPHONE: _perform_command_next_homophone,
    CommandType.REPLACE: _perform_command_replace,
    CommandType.TITLE_CASE: _perform_command_title_case,
    CommandType.LOWERCASE: _perform_command_lowercase,
    CommandType.REPLACE_WORD_MATCH_CASE: _perform_command_replace_word_match_case,
    CommandType.UPPERCASE: _perform_command_uppercase,
    CommandType.REPLACE_WITH_LAMBDA: _perform_command_replace_with_lambda,
}


def perform_command(command_type: CommandType, text: str, selection_range: TextRange,
                    match: TextMatch, insert_text: str, lambda_func: Optional[Callable[[str], str]],
                    utility_functions: UtilityFunctions) -> list[EditorAction]:
  """Gets the editor actions required to perform a command."""
  assert command_type in _COMMAND_FUNCTIONS
  if selection_range.end > len(text):
    raise ValueError(f"Selection beyond end of text: {selection_range}, Text Length: {len(text)}")
  if match.text_range.end > len(text):
    raise ValueError(f"From match beyond end of text: {match}")
  # Mypy error on next line is caused by "clear" command functions having extra optional parameters.
  return _COMMAND_FUNCTIONS[command_type](text, selection_range, match, insert_text, lambda_func,
                                          utility_functions)  # type: ignore[operator]
