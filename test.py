from game_engine import Minesweeper

from pyannotate_runtime import collect_types

collect_types.init_types_collection()

if __name__ == "__main__":
    collect_types.start()
    board: Minesweeper = Minesweeper("intermediate")
    board.random_safe_reveal()

    counter: int = 0
    while not (board.game_won or board.game_over):
        # print(counter)
        _, b = board.solve_minefield()
        board.random_safe_reveal()
        counter += 1
        # print(a, b)
        # break
    collect_types.stop()
    collect_types.dump_stats("type_info.json")
