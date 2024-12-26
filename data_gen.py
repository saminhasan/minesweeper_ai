import numpy as np
from game_engine import Minesweeper


def get_input(board: Minesweeper) -> np.ndarray:
    display_array: np.ndarray = np.full_like(board.minefield["mine_count"], -1)
    display_array[board.minefield["state"] == board.states.UNCOVERED.value] = (
        board.minefield["mine_count"][
            board.minefield["state"] == board.states.UNCOVERED.value
        ]
    )
    print(type(display_array), display_array.shape, board.shape)
    return display_array


def get_output(board: Minesweeper) -> np.ndarray:
    _, probability = board.solve_minefield()
    probability[board.minefield["state"] == board.states.UNCOVERED.value] = 0
    print(type(probability), probability.shape, board.shape)
    return probability


if __name__ == "__main__":
    board: Minesweeper = Minesweeper("easy")
    counter: int = 0
    while (not (board.game_won or board.game_over)) and counter < 10:
        board.random_safe_reveal()
        print(get_input(board=board))
        print(get_output(board=board))
        print(counter)
        break
