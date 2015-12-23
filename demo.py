import minesweeper as ms
import minesweeperAI as AI

config = ms.GameConfig()

ai = AI.AI()
viz = ms.GameVisualizer(1)

num_games = 1
if False:
    num_games = 1
    results = ms.run_games(config, num_games, ai, viz)
else:
    num_games = 1000
    results = ms.run_games(config, num_games, ai)

wins = 0
total_seconds = 0.0
for r in results:
    if r.success:
        wins += 1
    total_seconds += r.duration

avg_seconds = total_seconds / num_games

print '---------------- Stats ----------------'
print('win ratio: {0}'.format(float(wins) / num_games))
print('w-l-t: {0}-{1}-{2}'.format(wins, num_games - wins, num_games))
print('average duration: {0}s'.format(avg_seconds))
print('total duration: {0}s'.format(total_seconds))

raw_input()
viz.finish()
