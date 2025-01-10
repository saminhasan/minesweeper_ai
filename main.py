import asyncio
import pygame as pg
import pygame.locals
from typing import Tuple, Dict, Set
from game_engine import Minesweeper


FONT_SIZE: int = 20
CELL_SIZE: int = 56
LW: int = 1

levels: Dict = {
    0: "test",
    1: "easy",
    2: "intermediate",
    3: "hard",
}


def get_rgb(value: float) -> Tuple[int, int, int]:
    """
    Maps a value in [0, 1] to an RGB color.
    Parameters:
        value (float): A value between 0 and 1.
    Returns:
        Tuple[int, int, int]: RGB color as integers in the range [0, 255].
    """
    if not 0 <= value <= 1:
        raise ValueError("Value must be between 0 and 1")

    return (int(255 * (2 * value)) if value <= 0.5 else 255, 255 if value <= 0.5 else int(255 * (2 * (1 - value))), 0)


class GUI:
    def __init__(self, level: str):
        self.level: str = levels[level]  # Store the level for resetting the game
        self.initialize_game()

    def initialize_game(self):
        self.help = False
        self.board = Minesweeper(self.level)  # Calculate dimensions
        # self.board.random_safe_reveal()
        self.cell_size = CELL_SIZE
        self.rect_size = int(self.cell_size)
        self.line_width = LW
        vlines = self.board.n_cols + 1
        hlines = self.board.n_rows + 1
        self.width = (self.cell_size * self.board.n_cols) + (vlines * self.line_width)
        self.height = (self.cell_size * self.board.n_rows) + (hlines * self.line_width)

        # Define colors
        self.mine_color = (255, 0, 0)  # Red for mines
        self.uncovered_color = (0, 0, 0)  # Black for uncovered cells
        self.covered_color = (80, 80, 80)  # Light grey for covered cells
        self.text_color = (220, 220, 220)  # White text
        self.line_color = (30, 30, 30)  # White color for lines

        self.best_move = None

        self.running = True
        self.fps = 240

        pg.init()
        pg.font.init()
        self.mine_image: pg.Surface = pg.image.load("mine.png")  # Load icon image
        # Scale the mine image to fit the cell size
        self.scaled_mine_image = pg.transform.scale(self.mine_image, (self.cell_size, self.cell_size))
        self.flag_image = pg.image.load("flag.png")
        self.scaled_flag_image = pg.transform.scale(self.flag_image, (self.cell_size // 1.5, self.cell_size // 1.5))
        pg.display.set_icon(self.mine_image)  # Set the icon for the window
        self.font = pg.font.Font(None, FONT_SIZE)  # Default font in PyGBag
        self.overlay_font = pg.font.Font(None, min(self.width // 15, self.height // 15))
        self.clock = pg.time.Clock()
        self.screen = pg.display.set_mode((self.width, self.height))
        pg.display.set_caption("Minesweeper")
        self.flagged: Set[Tuple[int, int]] = set()

    def handle_events(self):
        for event in pg.event.get():
            if event.type == pg.QUIT:
                self.quit()
            elif event.type == pg.KEYDOWN:
                self.handle_key_event(event.key)
            # elif event.type in [pg.MOUSEBUTTONDOWN, pg.MOUSEBUTTONUP]:
            elif event.type in [pg.MOUSEBUTTONDOWN]:
                self.handle_mouse_event(event)

    def handle_key_event(self, key):
        if key == pg.K_r:
            self.reset_game()
        elif key == pg.K_h:
            self.help = not self.help
            if self.help:
                _, self.probability = self.board.solve_minefield()

        elif key in [pg.K_0, pg.K_1, pg.K_2, pg.K_3]:
            self.level = levels[key - pg.K_0]
            self.reset_game()
        else:
            handler = self.key_event_handlers.get(key)
            if handler:
                handler()

    def handle_mouse_event(self, event):
        if not self.board.game_over or self.board.game_won:
            if event.type == pg.MOUSEBUTTONDOWN:
                col = (event.pos[0] - self.line_width) // (self.cell_size + self.line_width)
                row = (event.pos[1] - self.line_width) // (self.cell_size + self.line_width)
                # Check if the click is within the bounds of the board
                if 0 <= row < self.board.n_rows and 0 <= col < self.board.n_cols:
                    if event.button == pg.BUTTON_LEFT:  # Left click
                        if (row, col) not in self.flagged:
                            if self.board.minefield[row][col]["mine_count"] == -1:
                                self.board.reveal_all_mines()
                                print("Game Over")
                            else:
                                self.board.reveal(row, col)
                                _, self.probability = self.board.solve_minefield()
                                self.flagged = {
                                    flag
                                    for flag in self.flagged
                                    if self.board.minefield[flag[0]][flag[1]]["state"] != self.board.states.UNCOVERED
                                }

                    if event.button == pg.BUTTON_RIGHT:
                        if (row, col) not in self.flagged:
                            self.flagged.add((row, col))
                        else:
                            self.flagged.discard((row, col))

    def draw(self):
        self.screen.fill([0, 0, 0])  # Background color
        self.draw_lines()

        # Check for game over or won condition
        if self.board.game_won:
            self.draw_cells()
            self.draw_flags()
            main_text = "Game Won, Press 'R' to Restart"
            # Create a transparent overlay surface
            overlay = pygame.Surface(self.screen.get_size(), pygame.SRCALPHA)
            overlay.fill((0, 64, 0, 64))  # Semi-transparent green background
            self.screen.blit(overlay, (0, 0))

        elif self.board.game_over:
            self.draw_mines()
            main_text = "Game Over, Press 'R' to Restart"
            # Create a transparent overlay surface
            overlay = pygame.Surface(self.screen.get_size(), pygame.SRCALPHA)
            overlay.fill((64, 0, 0, 64))  # Semi-transparent green background
            self.screen.blit(overlay, (0, 0))

        else:
            self.draw_cells()
            self.draw_bayes()
            return

        # Render main message
        main_text_surface = self.overlay_font.render(main_text, True, (255, 255, 255))  # White text
        main_text_rect = main_text_surface.get_rect(center=(self.width // 2, self.height // 3))

        level_text = f"Current Level: {self.level.capitalize()}"  # Capitalize level string
        level_surface = self.overlay_font.render(level_text, True, (255, 255, 255))
        level_rect = level_surface.get_rect(center=(self.width // 2, self.height // 2))

        options_text = "Press 1 - Easy, 2 - Intermediate, 3 - Hard"
        options_surface = self.overlay_font.render(options_text, True, (255, 255, 255))
        options_rect = options_surface.get_rect(center=(self.width // 2, (2 * self.height) // 3))

        # Draw everything
        self.screen.blit(main_text_surface, main_text_rect)
        self.screen.blit(level_surface, level_rect)
        self.screen.blit(options_surface, options_rect)

    def draw_cells(self):
        # Other parameters
        corner_radius = self.cell_size // 5
        offset = 5

        # Draw the cells
        for row in range(self.board.n_rows):
            for col in range(self.board.n_cols):
                x = col * (self.cell_size + self.line_width) + self.line_width
                y = row * (self.cell_size + self.line_width) + self.line_width
                cell = self.board.minefield[row][col]
                rect_x, rect_y = x + offset, y + offset
                rect_size = self.cell_size - (2 * offset)
                if cell["state"] == self.board.states.COVERED:
                    pg.draw.rect(
                        self.screen,
                        self.covered_color,
                        (rect_x, rect_y, rect_size, rect_size),
                        border_radius=corner_radius,
                    )
                    # Check if the cell is flagged
                    if (row, col) in self.flagged:
                        # Center the flag image within the cell
                        center_x = rect_x + rect_size // 2 - self.scaled_flag_image.get_width() // 2
                        center_y = rect_y + rect_size // 2 - self.scaled_flag_image.get_height() // 2

                        self.screen.blit(self.scaled_flag_image, (center_x, center_y))
                if cell["state"] == self.board.states.UNCOVERED:
                    if cell["mine_count"] > 0:
                        text_surface = self.font.render(f"{cell['mine_count']}", True, self.text_color)
                        text_rect = text_surface.get_rect(
                            center=(
                                rect_x + rect_size // 2,
                                rect_y + rect_size // 2,
                            )
                        )
                        self.screen.blit(text_surface, text_rect)

    def draw_bayes(self):
        if self.help:
            # Other parameters
            corner_radius = self.cell_size // 5
            offset = 5
            # Draw the cells
            for row in range(self.board.n_rows):
                for col in range(self.board.n_cols):
                    x = col * (self.cell_size + self.line_width) + self.line_width
                    y = row * (self.cell_size + self.line_width) + self.line_width
                    cell = self.board.minefield[row][col]

                    # Adjust dimensions to include the offset
                    rect_x, rect_y = x + offset, y + offset
                    rect_size = self.cell_size - (2 * offset)

                    if not cell["state"] == self.board.states.UNCOVERED:
                        if self.probability is not None:
                            if self.probability[row][col] == 0:
                                pg.draw.rect(
                                    self.screen,
                                    pg.Color("green"),
                                    (rect_x, rect_y, rect_size, rect_size),
                                    border_radius=corner_radius,
                                )
                            elif self.probability[row][col] == 1:
                                center_x = rect_x + rect_size // 2 - self.scaled_flag_image.get_width() // 2
                                center_y = rect_y + rect_size // 2 - self.scaled_flag_image.get_height() // 2

                                self.screen.blit(self.scaled_flag_image, (center_x, center_y))
                            else:
                                pg.draw.rect(
                                    self.screen,
                                    self.covered_color,
                                    (rect_x, rect_y, rect_size, rect_size),
                                    border_radius=corner_radius,
                                )
                                text_surface = self.font.render(
                                    f"{self.probability[row][col]:.2f}",
                                    True,
                                    get_rgb(self.probability[row][col]),
                                )
                                text_rect = text_surface.get_rect(
                                    center=(
                                        rect_x + rect_size // 2,
                                        rect_y + rect_size // 2,
                                    )
                                )

                                self.screen.blit(text_surface, text_rect)

    def draw_lines(self):
        gap_size = self.cell_size // 8

        # Draw lines with gaps
        for col in range(1, self.board.n_cols):
            x = col * (self.cell_size + self.line_width)
            for row in range(self.board.n_rows):
                y_start = row * (self.cell_size + self.line_width)
                y_end = y_start + self.cell_size
                pg.draw.line(
                    self.screen,
                    self.line_color,
                    (x, y_start + gap_size),
                    (x, y_end - gap_size),
                    self.line_width,
                )

        for row in range(1, self.board.n_rows):
            y = row * (self.cell_size + self.line_width)
            for col in range(self.board.n_cols):
                x_start = col * (self.cell_size + self.line_width)
                x_end = x_start + self.cell_size
                pg.draw.line(
                    self.screen,
                    self.line_color,
                    (x_start + gap_size, y),
                    (x_end - gap_size, y),
                    self.line_width,
                )

    def draw_mines(self):
        """
        Draw the mines on the Minesweeper board.
        """

        # Draw the mines
        for row in range(self.board.n_rows):
            for col in range(self.board.n_cols):
                x = col * (self.cell_size + self.line_width) + self.line_width
                y = row * (self.cell_size + self.line_width) + self.line_width
                cell = self.board.minefield[row][col]
                rect_x, rect_y = x, y
                rect_size = self.cell_size

                # Check if the cell contains a mine
                if cell["mine_count"] == -1:
                    # Center the mine image within the cell
                    center_x = rect_x + rect_size // 2 - self.scaled_mine_image.get_width() // 2
                    center_y = rect_y + rect_size // 2 - self.scaled_mine_image.get_height() // 2

                    self.screen.blit(self.scaled_mine_image, (center_x, center_y))

    def draw_flags(self):
        """
        Draw the mines on the Minesweeper board.
        """

        # Draw the mines
        for row in range(self.board.n_rows):
            for col in range(self.board.n_cols):
                x = col * (self.cell_size + self.line_width) + self.line_width
                y = row * (self.cell_size + self.line_width) + self.line_width
                cell = self.board.minefield[row][col]
                rect_x, rect_y = x, y
                rect_size = self.cell_size

                # Check if the cell contains a mine
                if cell["mine_count"] == -1:
                    # Center the mine image within the cell
                    center_x = rect_x + rect_size // 2 - self.scaled_flag_image.get_width() // 2
                    center_y = rect_y + rect_size // 2 - self.scaled_flag_image.get_height() // 2

                    self.screen.blit(self.scaled_flag_image, (center_x, center_y))

    def quit(self):
        self.running = False

    def reset_game(self):
        self.initialize_game()


async def main():
    game = GUI(1)

    try:
        while game.running:
            game.handle_events()
            game.draw()
            pg.display.update()
            await asyncio.sleep(0)  # Yield control to the event loop
    except Exception as e:
        print(e)
    finally:
        game.quit()
    pg.quit()


if __name__ == "__main__":
    asyncio.run(main())
