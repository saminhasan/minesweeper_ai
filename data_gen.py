import numpy as np
from game_engine import Minesweeper


def get_input(board: Minesweeper):
    display_array = np.full_like(board.minefield["mine_count"], -1)
    display_array[board.minefield["state"] == board.states.UNCOVERED.value] = (
        board.minefield["mine_count"][
            board.minefield["state"] == board.states.UNCOVERED.value
        ]
    )
    return display_array


def get_output(board: Minesweeper):
    _, probability = board.solve_minefield()
    return probability


if __name__ == "__main__":
    board: Minesweeper = Minesweeper("easy")
    counter: int = 0
    while (not (board.game_won or board.game_over)) and counter < 10:
        board.random_safe_reveal()
        print(get_input(board=board))
        print(get_output(board=board))
        counter += 1
        # print(a, b)
        print(counter)
