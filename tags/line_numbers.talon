tag: user.line_numbers
-
jump line <user.number>: user.jump_line(number)
(pour|float) line <user.number>:
  user.jump_line(number)
  user.line_insert_down()
(drink|spike) line <user.number>:
  user.jump_line(number)
  user.line_insert_up()
pick line <user.number> [past <user.number>]:
  user.select_line_range_including_line_break(number_1, number_2 or 0)
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
bring line <user.number> [past <user.number>]: user.bring_line_range(number_1, number_2 or 0)
