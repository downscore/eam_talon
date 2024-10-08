tag: user.line_numbers
-
line <user.number>: user.jump_line(number)
pour line <user.number>:
  user.jump_line(number)
  user.line_insert_down()
drink line <user.number>:
  user.jump_line(number)
  user.line_insert_up()
spike line <user.number>: user.line_numbers_insert_line_above_no_move(number)
float line <user.number>: user.line_numbers_insert_line_below_no_move(number)
pick line <user.number> [past <user.number>]:
  user.select_line_range_for_editing(number_1, number_2 or 0)
chuck line <user.number> [past <user.number>]:
  user.select_line_range_including_line_break(number_1, number_2 or 0)
  user.delete()
copy line <user.number> [past <user.number>]:
  user.select_line_range_including_line_break(number_1, number_2 or 0)
  user.clipboard_history_copy()
  user.right()
cut line <user.number> [past <user.number>]:
  user.select_line_range_including_line_break(number_1, number_2 or 0)
  user.clipboard_history_cut()
  user.right()
indent line <user.number> [past <user.number>]:
  user.select_line_range_including_line_break(number_1, number_2 or 0)
  user.indent_more()
  user.right()
dedent line <user.number> [past <user.number>]:
  user.select_line_range_including_line_break(number_1, number_2 or 0)
  user.indent_less()
  user.right()
bring line <user.number> [past <user.number>]:
  user.line_numbers_bring_line_range(number_1, number_2 or 0)

# Scrambler commands using line numbers.
<user.scrambler_command_type> line <user.number> <user.scrambler_any_match>:
  user.splits_line_numbers_scrambler_run_command(number, scrambler_command_type, scrambler_any_match, false)
