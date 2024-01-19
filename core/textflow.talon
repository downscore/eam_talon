# Single compound target command.
<user.textflow_command_type> <user.textflow_compound_target>:
  user.textflow_execute_command(textflow_command_type, textflow_compound_target)

# Command on the current block.
<user.textflow_command_type> block:
  user.textflow_execute_command_current_block(textflow_command_type)

# Command on a line.
<user.textflow_command_type> row <user.textflow_simple_target>:
  user.textflow_execute_line_command(textflow_command_type, textflow_simple_target)

# Command starting from the cursor.
<user.textflow_command_type> <user.textflow_target_combo_type> <user.textflow_simple_target>:
  user.textflow_execute_command_from_cursor(textflow_command_type, textflow_target_combo_type, textflow_simple_target)

# Commands that act on a single word target.
<user.textflow_single_word_command_type> <user.textflow_word>:
  user.textflow_execute_command(textflow_single_word_command_type, textflow_word)

# Insert newline relative to target.
drink <user.textflow_simple_target>:
  user.textflow_new_line_above(textflow_simple_target)
pour <user.textflow_simple_target>:
  user.textflow_new_line_below(textflow_simple_target)

# Replace a target with prose (includes punctuation).
replace <user.textflow_compound_target> with <user.prose>$:
  user.textflow_replace(textflow_compound_target, prose)
replace <user.textflow_compound_target> with <user.prose> anchor:
  user.textflow_replace(textflow_compound_target, prose)

# Single word replacement.
swap <user.textflow_word> with <user.word>:
  user.textflow_replace_word(textflow_word, word)

# Segmenting or joining words.
segment <user.word> <user.word>:
  user.textflow_segment_word(word_1, word_2)
join up <user.word> <user.word>:
  user.textflow_join_words(word_1, word_2)
hyphenate <user.word> <user.word>:
  user.textflow_hyphenate_words(word_1, word_2)

# Swapping articles (the <-> a).
definite [<user.ordinals_small>] [{user.textflow_search_direction}]:
  user.textflow_switch_to_definite(ordinals_small or 1, textflow_search_direction or "")
indefinite [<user.ordinals_small>] [{user.textflow_search_direction}]:
  user.textflow_switch_to_indefinite(ordinals_small or 1, textflow_search_direction or "")
