#!/usr/bin/env python3

# Instructions:
# 1. Create the puzzle by filling in the light/dark squares
# 2. Autofill then accept hints
# 3. Save file

from pathlib import Path
from optparse import OptionParser
import string
import random
import copy
import sys

import qxw

try: 
  from BeautifulSoup import BeautifulSoup
except ImportError:
  from bs4 import BeautifulSoup

# TODO: grid-template-rows for words shouldn't be hard-coded
css = '''
:root {
  --border-size: 1px;
  --cell-width: calc(36px - var(--border-size));
  --cell-height: calc(36px - var(--border-size));
	--workspace-width: calc(3 * (var(--cell-width) + var(--border-size)));
	--number-font-size: 12px;
	--letter-font-size: 22px;
}
body { font-family: sans-serif; }
.title { text-align: center; }
main-grid { display: grid; grid-template-columns: var(--workspace-width) var(--workspace-width) 1fr 1fr; column-gap: 1em; }
puzzle { display: grid; gap: var(--border-size); grid-auto-flow: row; grid-auto-rows: var(--cell-height); position: relative; }
workspace { display: grid; gap: var(--border-size); grid-auto-flow: column; grid-template-rows: repeat(13, var(--cell-height)); grid-auto-columns: var(--cell-width); }
sq { outline: var(--border-size) solid black; position: relative}
.bk { background-color: black; }
nu { z-index: 0; display: block; text-align: left; font-size: var(--number-font-size); margin-top: -3px; margin-left: 0px; width: 100%; height: 100%; position: absolute;}
lt { z-index: 1; display: block; text-align: center; font-size: var(--letter-font-size); width: 100%; height: 100%; position: absolute;}
puzzle lt { top: 2px; }
words { display: grid; grid-template-rows: repeat(24, 1fr); grid-auto-flow: column; grid-auto-columns: max-content; column-gap: 1em; margin-left: 2em; }
word { }
'''

class HTMLGenerator:
  def __init__(self, width, height, letters, title):
    self.doc = BeautifulSoup('<html><head></head><body></body></html>', 'lxml')
    self.width = width
    self.height = height
    self.title = title
    self.square_count = 0

    if title:
      e_title = self.doc.new_tag('title')
      e_title.string = title
      self.doc.head.append(e_title)

      e_title_heading = self.doc.new_tag('h1')
      e_title_heading['class'] = 'title'
      e_title_heading.string = title
      self.doc.body.append(e_title_heading)

    style = self.doc.new_tag('style', type='text/css')
    style.string = css
    self.doc.head.append(style)

    self.e_main_grid = self.doc.new_tag('main-grid')
    self.e_main_grid.append("\n")
    self.doc.body.append(self.e_main_grid)

    e_workspace_nu = self.doc.new_tag('workspace')
    for i in range(0, 26):
      e_square = self.doc.new_tag('sq')
      e_nu = self.doc.new_tag('nu')
      e_nu.string = str(i + 1)
      e_square.append(e_nu)
      e_workspace_nu.append(e_square)

    self.e_main_grid.append(e_workspace_nu)
    self.e_main_grid.append("\n")

    e_workspace_lt = self.doc.new_tag('workspace')
    for i in range(0, 26):
      e_square = self.doc.new_tag('sq')
      e_lt = self.doc.new_tag('lt', attrs={'style':'font-weight:bold'})
      e_lt.string = letters[i]
      e_square.append(e_lt)
      e_workspace_lt.append(e_square)

    self.e_main_grid.append(e_workspace_lt)
    self.e_main_grid.append("\n")

    self.e_puzzle = self.doc.new_tag('puzzle', style=f'grid-template-columns:repeat({width}, var(--cell-width))')
    self.e_puzzle.append("\n")
    self.e_main_grid.append(self.e_puzzle)
    self.e_main_grid.append("\n")

    self.e_words = self.doc.new_tag('words')
    self.e_main_grid.append(self.e_words)
    self.e_main_grid.append("\n")

  def add_square(self, sq, codex, reveal):
    e_square = self.doc.new_tag('sq')
    if sq.blocked:
      e_square['class'] = 'bk'
    if sq.letter != '' and sq.letter != '.': # TODO: this logic belongs in qxw.py
      e_nu = self.doc.new_tag('nu')
      e_nu.string = str(codex[sq.letter])
      e_square.append(e_nu)
    if reveal:
      e_lt = self.doc.new_tag('lt')
      e_lt.string = sq.letter
      e_square.append(e_lt)
    self.e_puzzle.append(e_square)

    self.square_count += 1
    if self.square_count % self.width == 0:
      self.e_puzzle.append("\n")

  def add_words(self, words):
    for word in words:
      # word = word.replace('_', '&ThinSpace;_&ThinSpace;')
      word = word.replace('_', '\u2009_\u2009')
      e_word = self.doc.new_tag('word')
      e_word.string = word
      self.e_words.append(e_word)


def find_not_blocked_squares(puzzle):
  width = puzzle.grid_properties.width
  height = puzzle.grid_properties.height

  not_blocked = [ ]
  for y in range(0, height):
    for x in range(0, width):
      sq = puzzle[x, y]
      if not sq.blocked: not_blocked.append((x, y))

  return not_blocked

def revealed_coords(puzzle):
  width = puzzle.grid_properties.width
  height = puzzle.grid_properties.height

  not_blocked = find_not_blocked_squares(puzzle)

  reveal = [ ]
  x, y = random.sample(not_blocked, k=1)[0]
  reveal.append((x, y))

  if x > 1 and not puzzle[x-1, y].blocked: reveal.append((x-1, y))
  elif y > 1 and not puzzle[x, y-1].blocked: reveal.append((x, y-1))
  elif x < width and not puzzle[x+1, y].blocked: reveal.append((x+1, y)) # TODO: this check can access a square that is in-bounds but not in the dict (saw it on a 17x17 with KeyError for 9)
  elif y < height and not puzzle[x, y+1].blocked: reveal.append((x, y+1))

  return reveal

def find_words_across(puzzle):
  width = puzzle.grid_properties.width
  height = puzzle.grid_properties.height

  words_across = [ ]
  for y in range(0, height):
    word = ''
    for x in range(0, width):
      sq = puzzle[x, y]
      if sq.blocked:
        if len(word) > 1: words_across.append(word)
        word = ''
      else:
        word += sq.letter
    if len(word) > 1: words_across.append(word)

  return words_across

def find_words_down(puzzle):
  width = puzzle.grid_properties.width
  height = puzzle.grid_properties.height

  words_down = [ ]
  for x in range(0, width):
    word = ''
    for y in range(0, height):
      sq = puzzle[x, y]
      if sq.blocked:
        if len(word) > 1: words_down.append(word)
        word = ''
      else:
        word += sq.letter
    if len(word) > 1: words_down.append(word)

  return words_down

def find_all_words(puzzle):
  words_across = find_words_across(puzzle)
  words_down = find_words_down(puzzle)
  words = sorted(words_across + words_down)
  return words

def make_codex(letters):
  by_code = list(letters)
  random.shuffle(by_code)
  codex = { letter: 1 + by_code.index(letter) for letter in letters }
  return codex

def hide_one_letter(word):
  r = random.randrange(0, len(word))
  return word[:r] + '_' + word[r + 1:]

def hide_letters(words, hidden_letters):
  words = [ hide_one_letter(word) for word in words ]
  table = str.maketrans({ letter : '_' for letter in hidden_letters })
  words = [ word.translate(table) for word in words ]
  return words

def parse_args(argv):
  parser = OptionParser()
  parser.add_option('-t', '--title', dest='title')
  parser.add_option('--chance-hide-letters-in-revealed-words', type=float, default=0.5)
  opts, args = parser.parse_args(argv)
  return opts, args

def main(argv):
  opts, args = parse_args(argv)
  print('Opts:', opts, file=sys.stderr)

  puzzle = qxw.read_file(args[1])

  title = opts.title or puzzle.title
  width = puzzle.grid_properties.width
  height = puzzle.grid_properties.height

  reveal = revealed_coords(puzzle)

  letters = list(string.ascii_uppercase)
  codex = make_codex(letters)

  gen = HTMLGenerator(width, height, letters, title)

  for y in range(0, height):
    for x in range(0, width):
      sq = puzzle[x, y]
      gen.add_square(sq, codex, (x, y) in reveal)

  words = find_all_words(puzzle)

  revealed_letters = [ puzzle[x, y].letter for x, y in reveal ]

  # TODO: if I forget to accept autofill hints, then I get an exception.
  # This fixes the exception but then the puzzle is blank.
  # revealed_letters = [ c for c in revealed_letters if c != '' ]

  revealed_words = [ ]
  for word in words:
    count = 0
    for letter in set(revealed_letters):
      count += word.count(letter)
    if count > 1:
      revealed_words.append(word)

  hidden_letters = set(revealed_letters)

  # TODO: This either hides too few letters or doesn't hide enough
  # letters.  Need a better heuristic for deciding which letters in a
  # word to hide.
  for word in revealed_words:
    if random.uniform(0, 1) < opts.chance_hide_letters_in_revealed_words:
      hidden_letters.update(word)


  print('## before hiding letters:', words, file=sys.stderr)
  words = hide_letters(words, hidden_letters)
  print('## after hiding letters:', words, file=sys.stderr)
  gen.add_words(words)

  print(gen.doc)
  sys.stdout.flush()

  print('revealed', reveal, file=sys.stderr)
  for x, y in reveal:
    sq = puzzle[x, y]
    print(sq, file=sys.stderr)

  print('revealed words', revealed_words, file=sys.stderr)
  print('hidden letters', hidden_letters, file=sys.stderr)

if __name__ == '__main__':
  main(sys.argv)
