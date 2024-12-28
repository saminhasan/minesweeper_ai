from game_engine import Minesweeper

if __name__ == "__main__":
    board: Minesweeper = Minesweeper("intermediate")
    counter: int = 0
    while not (board.game_won or board.game_over):
        print(counter)
        board.random_safe_reveal()
        a, b = board.solve_minefield()
        counter += 1
        # print(a, b)
