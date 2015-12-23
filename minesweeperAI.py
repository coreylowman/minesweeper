import minesweeper as ms
import random

# games: 5000
# 8x8, 10 mines:    0.5416
# 9x9, 10 mines:    -
# 16x16, 40 mines:  -
# 16x30, 99 mines:  -


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
    DEBUG = False

    def __init__(self):
        self.width = 0
        self.height = 0
        self.bombs_left = 0
        self.total_squares_left = 0
        self.firstPick = True
        self.squares = list()
        self.groups = list()
        self.flags = list()
        self.exposedSquares = list()

    def init(self, config):
        self.width = config.width
        self.height = config.height
        self.bombs_left = config.num_mines
        self.total_squares_left = self.width * self.height
        self.firstPick = True
        self.squares = [[Square() for _ in xrange(self.height)] for _ in xrange(self.width)]
        del self.groups[:]
        del self.flags[:]
        del self.exposedSquares[:]

    def next(self):
        # creating groups
        del self.groups[:]
        for (i, j) in self.exposedSquares:
            unmarked_around = self._unmarked_around(i, j)
            g = Group((i, j), self.squares[i][j].neighboringBombs)
            g.squares += unmarked_around
            self.groups.append(g)

        # marking bombs
        for (i, j) in self.exposedSquares:
            unmarked_around = self._unmarked_around(i, j)
            if len(unmarked_around) == self.squares[i][j].neighboringBombs:
                for (x, y) in unmarked_around:
                    self._log('marking {0},{1}: #uncleared == #neighbors'.format(x, y))
                    self._mark_bomb_at(x, y)
            else:
                bombs = self.squares[i][j].neighboringBombs
                for g in self.groups:
                    if g.is_next_to_pos(i, j):
                        unmarked_around = [item for item in unmarked_around if item not in g.squares]
                        bombs -= g.num_bombs
                if bombs == len(unmarked_around):
                    for (x, y) in unmarked_around:
                        self._log('marking {0},{1}: #(uncleared - groups) == #(neighbors - groups)'.format(x, y))
                        self._mark_bomb_at(x, y)

        # selecting squares
        for (i, j) in self.exposedSquares:
            unmarked_around = self._unmarked_around(i, j)
            if self.squares[i][j].neighboringBombs == 0 and len(unmarked_around) > 0:
                x, y = self._unmarked_around(i, j).pop()
                self._log('selecting {0},{1}: all bombs are accounted for'.format(x, y))
                return x, y
            else:
                bombs = self.squares[i][j].neighboringBombs
                for g in self.groups:
                    if g.is_next_to_pos(i, j):
                        unmarked_around = [item for item in unmarked_around if item not in g.squares]
                        bombs -= g.num_bombs
                if bombs == 0 and len(unmarked_around) > 0:
                    x, y = unmarked_around.pop()
                    self._log('selecting {0},{1}: groups account for all bombs'.format(x, y))
                    return x, y

        # calculating simple chance of bomb around a square
        lowestChance = 1.0
        for (i, j) in self.exposedSquares:
            unmarked_around = self._unmarked_around(i, j)
            if len(unmarked_around) == 0:
                continue
            chance = float(self.squares[i][j].neighboringBombs) / float(len(unmarked_around))
            if chance < lowestChance and not self.squares[i][j].isExposed:
                x, y = unmarked_around[random.randint(0, len(unmarked_around) - 1)]
                lowestChance = chance

        # choosing the simple chance or randomly
        defaultChance = float(self.bombs_left) / float(self.total_squares_left)
        if lowestChance <= defaultChance:
            self._log('selecting {0},{1}: by lowest chance {2}'.format(x, y, lowestChance))
            return x, y
        else:
            # picking corners first increases win rate??
            corners = [(0, 0), (0, self.height - 1), (self.width - 1, 0), (self.width - 1, self.height - 1)]
            for (x, y) in corners:
                if not self.squares[x][y].isExposed and not self.squares[x][y].markedAsBomb:
                    self._log('selecting {0},{1}: picking corner.'.format(x, y))
                    return x, y
            while True:
                x = random.randint(0, self.width - 1)
                y = random.randint(0, self.height - 1)
                if not self.squares[x][y].isExposed and not self.squares[x][y].markedAsBomb:
                    self._log('selecting {0},{1}: picking randomly. {2} chance of bomb'.format(x, y, defaultChance))
                    return x, y

    def update(self, result):
        # note the '+=' with updating neighboringBombs to conserve the number
        #   of bombs already found around the square
        for position in result.new_squares:
            self.squares[position.x][position.y].isExposed = True
            self.squares[position.x][position.y].neighboringBombs += position.num_bomb_neighbors
            self.total_squares_left -= 1
            self.exposedSquares.append((position.x, position.y))

    def get_flags(self):
        return self.flags

    def _log(self, q, force=False):
        if(force or self.DEBUG):
            print(q)

    def _mark_bomb_at(self, x, y):
        if self.bombs_left == 0 or self.squares[x][y].markedAsBomb:
            return
        self.squares[x][y].markedAsBomb = True
        self.flags.append((x, y))
        self.total_squares_left -= 1
        self.bombs_left -= 1
        for i in [-1, 0, 1]:
            for j in [-1, 0, 1]:
                new_x, new_y = x + i, y + j
                if self._in_board(new_x, new_y):
                    self.squares[new_x][new_y].neighboringBombs -= 1

    def _in_board(self, x, y):
        return 0 <= x and x < self.width and 0 <= y and y < self.height

    def _unmarked_around(self, x, y):
        neighbors = [(x-1, y-1), (x-1, y), (x-1, y+1), (x, y-1), (x, y+1), (x+1, y-1), (x+1, y), (x+1, y+1)]
        result = []
        for (i, j) in neighbors:
            if (self._in_board(i, j) and
                    not self.squares[i][j].isExposed and
                    not self.squares[i][j].markedAsBomb):
                result.append((i, j))
        return result
