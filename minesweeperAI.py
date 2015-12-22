import minesweeper as ms
import random

# games: 5000
# 8x8, 10 mines:    0.4472
# 9x9, 10 mines:    0.6242
# 16x16, 40 mines:  0.3704
# 16x30, 99 mines:  0.0272


class Square(object):
    def __init__(self):
        self.isExposed = False
        self.markedAsBomb = False
        self.neighboringBombs = 0


class Group(object):
    def __init__(self, pos, num_bombs):
        self.pos = pos
        self.num_bombs = num_bombs
        self.squares = list()  # list of square coordinates (x, y)

    def is_next_to_pos(self, x, y):
        if self.pos == (x, y):
            return False
        for (i, j) in self.squares:
            if abs(x - i) > 1 or abs(y - j) > 1:
                return False
        return True


class AI(ms.GameAI):
    DEBUG = True

    def __init__(self):
        self.width = 0
        self.height = 0
        self.mines = 0
        self.total_squares = 0
        self.firstPick = True
        self.squares = [[Square() for _ in xrange(self.height)] for _ in xrange(self.width)]
        self.groups = list()
        self.flags = list()

    def init(self, config):
        self.width = config.width
        self.height = config.height
        self.mines = config.num_mines
        self.total_squares = self.width * self.height
        self.firstPick = True
        self.squares = [[Square() for _ in xrange(self.height)] for _ in xrange(self.width)]
        del self.groups[:]
        del self.flags[:]

    def next(self):
        x = 0
        y = 0
        if self.firstPick:
            self.firstPick = False
            x = 0
            y = 0
            self._log('selecting {0},{1}: first pick top left corner'.format(x, y))
            return self._select(x, y)
        else:
            # marking bombs around squares that have the same number of squares
            # around them as bombs
            changed = True
            while changed:
                changed = False
                for i in xrange(self.width):
                    for j in xrange(self.height):
                        unmarked_around = self._unmarked_around(i, j)
                        if (self.squares[i][j].isExposed and
                                len(unmarked_around) == self.squares[i][j].neighboringBombs):
                                for (x, y) in unmarked_around:
                                    self._log('marking {0},{1}: uncleared == #neighbors'.format(x, y))
                                    changed = self._mark_bomb_at(x, y)

            # clearing around squares that have all bombs accounted for
            for i in xrange(self.width):
                for j in xrange(self.height):
                    unmarked_around = self._unmarked_around(i, j)
                    if (self.squares[i][j].isExposed and
                            self.squares[i][j].neighboringBombs == 0 and len(unmarked_around) > 0):
                        x, y = self._unmarked_around(i, j).pop()
                        self._log('selecting {0},{1}: all bombs are accounted for'.format(x, y))
                        return self._select(x, y)

            # creating groups
            del self.groups[:]
            for i in xrange(self.width):
                for j in xrange(self.height):
                    if self.squares[i][j].isExposed:
                        unmarked_around = self._unmarked_around(i, j)
                        g = Group((i, j), self.squares[i][j].neighboringBombs)
                        g.squares += unmarked_around
                        self.groups.append(g)

            # clearing or marking using groups
            for i in xrange(self.width):
                for j in xrange(self.height):
                    if self.squares[i][j].isExposed:
                        unmarked_around = self._unmarked_around(i, j)
                        bombs = self.squares[i][j].neighboringBombs
                        for g in self.groups:
                            if g.is_next_to_pos(i, j):
                                unmarked_around = [item for item in unmarked_around if item not in g.squares]
                                bombs -= g.num_bombs
                        if bombs == 0 and len(unmarked_around) > 0:
                            x, y = unmarked_around.pop()
                            self._log('selecting {0},{1}: groups account for all bombs'.format(x, y))
                            return self._select(x, y)
                        elif bombs == len(unmarked_around) and bombs == 0:
                            for (q, r) in unmarked_around:
                                self._log('marking {0},{1}: uncleared - groups == #(neighbors - groups)'.format(q, r))
                                self._mark_bomb_at(q, r)

            # calculating simple chance of bomb around a square
            lowestChance = 1.0
            for i in xrange(self.width):
                for j in xrange(self.height):
                    unmarked_around = self._unmarked_around(i, j)
                    if len(unmarked_around) == 0:
                        continue
                    # chance = 1 / float(2 << len(unmarked_around))
                    if not self.squares[i][j].isExposed:
                        continue
                    chance = float(self.squares[i][j].neighboringBombs) / float(len(unmarked_around))
                    if chance < lowestChance and not self.squares[i][j].isExposed:
                        x, y = unmarked_around[random.randint(0, len(unmarked_around) - 1)]
                        # x, y = i, j
                        lowestChance = chance

            # choosing the simple chance or randomly
            defaultChance = float(self.mines) / float(self.total_squares)
            if lowestChance <= defaultChance:
                self._log('selecting {0},{1}: by lowest chance {2}'.format(x, y, lowestChance))
                return self._select(x, y)
            else:
                while True:
                    x = random.randint(0, self.width - 1)
                    y = random.randint(0, self.height - 1)
                    if not self.squares[x][y].isExposed and not self.squares[x][y].markedAsBomb:
                        break
                self._log('selecting {0},{1}: picking randomly. {2} chance of bomb'.format(x, y, defaultChance))
                return self._select(x, y)

    def update(self, result):
        for position in result.new_squares:
            self.squares[position.x][position.y].isExposed = True
            # += to conserve the number of bombs already found around the square
            self.squares[position.x][position.y].neighboringBombs += position.num_bomb_neighbors

    def get_flags(self):
        return self.flags

    def _log(self, q, force=False):
        if(force or self.DEBUG):
            print(q)

    def _select(self, x, y):
        self.total_squares -= 1
        return x, y

    def _mark_bomb_at(self, x, y):
        if self.mines == 0 or self.squares[x][y].markedAsBomb:
            return False
        self.squares[x][y].markedAsBomb = True
        self.flags.append((x, y))
        self.total_squares -= 1
        self.mines -= 1
        for i in [-1, 0, 1]:
            for j in [-1, 0, 1]:
                new_x, new_y = x + i, y + j
                if self._in_board(new_x, new_y):
                    self.squares[new_x][new_y].neighboringBombs -= 1
        return True

    def _in_board(self, x, y):
        return 0 <= x and x < self.width and 0 <= y and y < self.height

    def _unmarked_around(self, x, y):
        unmarked = list()
        for i in [-1, 0, 1]:
            for j in [-1, 0, 1]:
                if i == 0 and j == 0:
                    continue
                new_x, new_y = x + i, y + j
                if (self._in_board(new_x, new_y) and
                        not self.squares[new_x][new_y].isExposed and
                        not self.squares[new_x][new_y].markedAsBomb):
                    unmarked.append((new_x, new_y))
        return unmarked
