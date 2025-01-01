import re
import sys
from collections import defaultdict
from dataclasses import dataclass, field

class GridProperties:
  def __init__(self, gtype, width, height, symmr, symmm, symmd):
    self.gtype = gtype    # 0=square, 1=hexH, 2=hexV, 3=circleA, 4=circleB,
                          # 5=cylinderLR, 6=cylinderTB, 7=moebiusLR,
                          # 8=moebuisTB, 9=torus
    self.width = width    # grid width
    self.height = height  # grid height
    self.symmr = symmr    # rotation symmetry
    self.symmm = symmm    # mirror symmetry
    self.symmd = symmd    # up/down left/righ symmetry

class LightProperties:
  def __init__(self, dmask, emask, ten, lpor, dnran=0, mux=0):
    self.dmask = dmask    # mask of allowed dictionaries
    self.emask = emask    # mask of allowed entry methods
    self.ten = ten        # treatment enable
    self.lpor = lpor      # global light property override
    self.dnran = dnran    # does not receive a number
    self.mux = mux        # is multiplexed

class SquareProperties:
  def __init__(self, bgcol, fgcol, ten, spor, fstyle, dech, mkcol):
    self.bgcol = bgcol    # background color
    self.fgcol = fgcol    # foreground color
    self.ten = ten        # treatment enable
    self.spor = spor      # global square property override
    self.fstyle = fstyle  # font style
    self.dech = dech      # de-checked (0=normal, 1=stacked, 2=side-by-side)
    self.mkcol = mkcol    # mark color
    self.mk = { }         # corner mark strings

class Treatment:
  def __init__(self, zero, treatmode, tambaw, treatorder_0, treatorder_1, tpinfo):
    self.zero = zero
    self.treatmode = treatmode
    self.tambaw = tambaw
    self.treatorder_0 = treatorder_0
    self.treatorder_1 = treatorder_1
    self.tpinfo = tpinfo
    self.msgs = { }

class Square:
  def __init__(self, bars, merge, fl, c=None):
    self.bars = bars      # bar presence in each direction
    self.merge = merge    # merge flags in each direction
    self.fl = fl          # flags (b0=blocked, b3=not part of grid, b4=selected)
    self.c = c            # should always be '.'
    self.properties = None
    self.contents = { }

  @property
  def blocked(self):
    return (self.fl & 1) != 0

  # TODO: this is wrong.  newer versions of qxw seem to always put the
  # letter into contents (i.e. SQCT), while older versions use both SQCT
  # (self.contents) and SQ (self.c).  I don't know the meaning of empty
  # string vs a period.
  # @property
  # def blank(self):
  #   # in older versions of qxw, c is the empty string; in newer
  #   # versions, it can also a dot.
  #   return self.c == '' or self.c == '.'

  @property
  def letter(self, layer=0):
    return self.contents[layer]

  def __str__(self):
    return repr(self)

  def __repr__(self):
    return f'Square({self.__dict__})'

class Dictionaries:
  def __init__(self):
    self.dfnames = { } # dictionary filenames
    self.dsfilters = { }
    self.dafilters = { }

@dataclass
class Puzzle:
  title: str | None = None
  author: str | None = None
  squares: defaultdict = field(default_factory=lambda: defaultdict(dict))
  grid_properties: GridProperties | None = None
  default_light_properties: LightProperties | None = None
  default_square_properties: SquareProperties | None = None
  treatment: Treatment | None = None
  dictionaries: Dictionaries = Dictionaries()

  def __getitem__(self, xy):
    x, y = xy
    return self.squares[x][y]

  def __setitem__(self, xy, square):
    x, y = xy
    self.squares[x][y] = square

  def __str__(self):
    return repr(self)

  def __repr__(self):
    return f'Puzzle({self.__dict__})'

def read(file):
  p = Puzzle()

  for line in file:
    if line[0] == '#': continue
    line = line.strip("\n")
    fields = re.split('\s+', line)
    cmd = fields[0]
    args = fields[1:]
    if cmd == 'GP':    p.grid_properties = GridProperties(*map(int, args))
    elif cmd == 'TTL': p.title = read_string(file)
    elif cmd == 'AUT': p.author = read_string(file)
    elif cmd == 'ALP': pass # TODO
    elif cmd == 'GLP': p.default_light_properties = LightProperties(*map(int, args))
    elif cmd == 'GSP': p.default_square_properties = SquareProperties(*args)
    elif cmd == 'GSPMK': p.default_square_properties.mk[int(args[0])] = read_string(file)
    elif cmd == 'TM': p.treatment = Treatment(*args, read_string(file))
    elif cmd == 'TMSG': p.treatment.msgs[int(args[1])] = read_string(file)
    elif cmd == 'TCST': pass # TODO
    elif cmd == 'DFN': p.dictionaries.dfnames[int(args[0])] = read_string(file)
    elif cmd == 'DSF': p.dictionaries.dsfilters[int(args[0])] = read_string(file)
    elif cmd == 'DAF': p.dictionaries.dafilters[int(args[0])] = read_string(file)
    elif cmd == 'SQ': p[map(int, args[0:2])] = Square(*map(int, args[2:-1]), args[-1])
    elif cmd == 'SQSP': p[map(int, args[0:2])].properties = SquareProperties(*args[2:])
    elif cmd == 'SQSPMK': file.readline() # TODO
    elif cmd == 'SQLP': pass # TODO
    elif cmd == 'VL': pass # TODO
    elif cmd == 'VLP': pass # TODO
    elif cmd == 'SQCT': p[map(int, args[0:2])].contents[int(args[2])] = args[3].replace('"', '') # TODO: not the best way to parse a quoted string
    elif cmd == 'END': break

  return p

def read_string(file):
  return file.readline().replace('+', '')

def read_file(filename):
  with open(filename) as file:
    return read(file)

if __name__ == '__main__':
  print('HERE')
  print(read_file(sys.argv[1]))

