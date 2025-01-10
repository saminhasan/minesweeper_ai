import random
import string
from dataclasses import dataclass
from solver import Rule, MineCount, solve
from typing import Tuple, Dict, List, Set, Union

# Type-hinted dictionary for game modes
game_mode: Dict[str, Dict[str, int]] = {
    "test": {"rows": 5, "columns": 5, "mines": 2},
    "easy": {"rows": 10, "columns": 10, "mines": 10},
    "intermediate": {"rows": 16, "columns": 16, "mines": 40},
    "hard": {"rows": 16, "columns": 40, "mines": 99},
}


@dataclass
class State:
    UNCOVERED = 0
    COVERED = -1
    # FLAGGED = 1


class TagGenerator:
    def __init__(self) -> None:
        self.chars: str = string.ascii_uppercase
        self.current: int = 0
        self.tag_length: int = 1

    def next_tag(self) -> str:
        if self.current >= len(self.chars) ** self.tag_length:
            self.tag_length += 1
            self.current = 0

        indices: List[int] = []
        temp: int = self.current
        for _ in range(self.tag_length):
            indices.append(temp % len(self.chars))
            temp //= len(self.chars)

        tag: str = "".join(self.chars[i] for i in reversed(indices))
        self.current += 1
        return tag


import random
from typing import List, Tuple, Set


class Minesweeper:
    def __init__(self, difficulty: str) -> None:
        self.game_over: bool = False
        self.game_won: bool = False
        self.states: type[State] = State
        self.n_rows: int = game_mode[difficulty]["rows"]
        self.n_cols: int = game_mode[difficulty]["columns"]
        self.shape: Tuple[int, int] = (self.n_rows, self.n_cols)
        self.n_mines: int = game_mode[difficulty]["mines"]

        # Replace NumPy array with a list of lists of dicts.
        self.minefield = [
            [{"mine_count": 0, "state": self.states.COVERED} for _ in range(self.n_cols)] for _ in range(self.n_rows)
        ]

        self.mines: Set[Tuple[int, int]] = set()
        self.place_mines()

    def place_mines(self) -> None:
        indices: List[Tuple[int, int]] = [(r, c) for r in range(self.n_rows) for c in range(self.n_cols)]

        for i, j in random.sample(indices, self.n_mines):
            self.mines.add((i, j))
            self.minefield[i][j]["mine_count"] = -1
            for r in range(max(0, i - 1), min(i + 2, self.n_rows)):
                for c in range(max(0, j - 1), min(j + 2, self.n_cols)):
                    if self.minefield[r][c]["mine_count"] != -1:
                        self.minefield[r][c]["mine_count"] += 1

    def reveal(self, i: int, j: int) -> None:
        if self.game_over or self.game_won:
            return

        # Use list indexing: self.minefield[i][j], not self.minefield[i, j]
        if self.minefield[i][j]["state"] != State.COVERED:
            return

        if self.minefield[i][j]["mine_count"] == -1:
            self.game_over = True
            self.reveal_all_mines()
            print("Game Over!")
            return

        # Mark this cell as uncovered
        self.minefield[i][j]["state"] = State.UNCOVERED

        # If the cell has no adjacent mines, recursively reveal neighbors
        if self.minefield[i][j]["mine_count"] == 0:
            for x in range(max(0, i - 1), min(i + 2, self.n_rows)):
                for y in range(max(0, j - 1), min(j + 2, self.n_cols)):
                    if (x, y) != (i, j) and not (self.game_over or self.game_won):
                        self.reveal(x, y)

        # Check if this reveal caused a win
        if self.check_win():
            self.game_won = True
            print("You won!")
            return

    def random_safe_reveal(self) -> None:
        # Generate a list of all covered cells that are not mines
        safe_cells: List[Tuple[int, int]] = [
            (i, j)
            for i in range(self.n_rows)
            for j in range(self.n_cols)
            if self.minefield[i][j]["state"] == State.COVERED and self.minefield[i][j]["mine_count"] != -1
        ]

        if not safe_cells:
            print("No safe cells to reveal.")
            return

        # Randomly pick one of those safe cells and reveal it
        i, j = random.choice(safe_cells)
        self.reveal(i, j)

    def reveal_all_mines(self) -> None:
        # For each mine location, mark its state as UNCOVERED
        for i, j in self.mines:
            self.minefield[i][j]["state"] = State.UNCOVERED
        self.game_over = True
        self.game_won = False

    def check_win(self) -> bool:
        return (
            len(
                [
                    (i, j)
                    for i in range(self.n_rows)
                    for j in range(self.n_cols)
                    if self.minefield[i][j]["state"] != State.UNCOVERED
                ]
            )
            == self.n_mines
        )

    def get_neighbors(self, i: int, j: int) -> List[Tuple[int, int]]:
        return [
            (x, y)
            for x in range(max(0, i - 1), min(i + 2, self.n_rows))
            for y in range(max(0, j - 1), min(j + 2, self.n_cols))
            if (x, y) != (i, j)
        ]

    def create_rules_from_minefield(self) -> Set[Rule]:
        rules: Set[Rule] = set()
        tags: Dict[Tuple[int, int], str] = {}
        tag_generator: TagGenerator = TagGenerator()
        self.tag_to_index: Dict[str, Tuple[int, int]] = {}

        for i in range(self.n_rows):
            for j in range(self.n_cols):
                if self.minefield[i][j]["state"] == State.UNCOVERED:
                    neighbors = self.get_neighbors(i, j)
                    mine_count: int = self.minefield[i][j]["mine_count"]

                    covered_neighbors: List[str] = []
                    for x, y in neighbors:
                        # Check if the neighbor is COVERED
                        neighbor_state = self.minefield[x][y]["state"]
                        if neighbor_state == State.COVERED:
                            # Assign a unique tag to this neighbor if needed
                            if (x, y) not in tags:
                                tag: str = tag_generator.next_tag()
                                tags[(x, y)] = tag
                                self.tag_to_index[tag] = (x, y)
                            covered_neighbors.append(tags[(x, y)])

                    if covered_neighbors:
                        # Create a rule like: "sum of these covered neighbors = mine_count"
                        rules.add(Rule(mine_count, covered_neighbors))

        return rules

    def decode_solution(
        self, solution: Dict[Union[str, None], float]
    ) -> Tuple[Dict[Tuple[int, int], float], List[List[float]]]:
        """
        Returns:
            decoded_solution: A dict mapping (row, col) -> probability
            probability_array: A 2D list of floats, same shape as minefield
        """
        decoded_solution: Dict[Tuple[int, int], float] = {}

        # 1) Determine the default value for each cell (e.g., 0.0 if solution[None] not present)
        default_prob: float = solution.get(None, 0.0)

        # 2) Create a 2D list initialized with this default probability
        probability_array: List[List[float]] = [[default_prob for _ in range(self.n_cols)] for _ in range(self.n_rows)]

        # 3) Fill in specific probabilities for tags that exist
        for tag, probability in solution.items():
            if tag in self.tag_to_index:
                i, j = self.tag_to_index[tag]
                decoded_solution[(i, j)] = probability
                probability_array[i][j] = probability

        return decoded_solution, probability_array

    def solve_minefield(self) -> Tuple[Dict[Tuple[int, int], float], List[List[float]]]:
        """
        Returns:
            (decoded_solution, probability_array):
            - decoded_solution: dict of (row, col) -> probability
            - probability_array: 2D list of probabilities
        """
        rules: Set[Rule] = self.create_rules_from_minefield()
        total_cells: int = self.n_rows * self.n_cols

        # 'solve' is presumably an external function that returns a dict like {tag: probability, ...}
        results: dict[str | None, float] | dict[str, float] = solve(
            rules, MineCount(total_cells=total_cells, total_mines=self.n_mines)
        )
        return self.decode_solution(results)


if __name__ == "__main__":
    board: Minesweeper = Minesweeper("intermediate")
    counter: int = 0
    while not (board.game_won or board.game_over):
        print(counter)
        board.random_safe_reveal()
        a, b = board.solve_minefield()
        counter += 1
        # print(a, b)
