import minesweeper as ms
import minesweeperAI as AI


config = ms.GameConfig()

ai = AI.AI()
viz = ms.GameVisualizer(0)

num_games = 1
if True:
    num_games = 1
    results = ms.run_games(config, num_games, ai, viz)
else:
    num_games = 1000
    results = ms.run_games(config, num_games, ai)

winRatio = 0.0
for r in results:
    if r.success:
        winRatio += 1
winRatio /= num_games

print winRatio

raw_input()
viz.finish()
