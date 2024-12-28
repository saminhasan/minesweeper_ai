import asyncio
import pygame as pg
import pygame.locals
from typing import Tuple
from game_engine import Minesweeper

levels = {
    0: "test",
    1: "easy",
    2: "intermediate",
    3: "hard",
}


class CustomColormap:
    def __init__(self):
        """
        Initializes a Green-Yellow-Orange-Red colormap with pre-defined RGB values.
        """
        self.colors = [
            (0, 255, 0),  # Green
            (255, 255, 0),  # Yellow
            (255, 128, 0),  # Orange
            (255, 0, 0),  # Red
        ]
        self.num_segments = len(self.colors) - 1

    def get_rgb(self, value: float) -> Tuple[int, int, int]:
        """
        Maps a value in [0, 1] to an RGB color.
        Parameters:
            value (float): A value between 0 and 1.
        Returns:
            Tuple[int, int, int]: RGB color as integers in the range [0, 255].
        """
        if not 0 <= value <= 1:
            raise ValueError("Value must be between 0 and 1")

        # Scale value to the number of segments
        scaled_value = value * self.num_segments
        idx = int(scaled_value)  # Find the segment index
        t = scaled_value - idx  # Fractional part within the segment

        # Get the start and end colors for interpolation
        color1 = self.colors[idx]
        color2 = self.colors[min(idx + 1, self.num_segments)]

        # Linear interpolation for each RGB channel
        r = int((1 - t) * color1[0] + t * color2[0])
        g = int((1 - t) * color1[1] + t * color2[1])
        b = int((1 - t) * color1[2] + t * color2[2])

        return r, g, b


colormap = CustomColormap()


class GUI:
    def __init__(self, level: str):
        self.level = levels[level]  # Store the level for resetting the game
        self.initialize_game()

    def initialize_game(self):
        self.board = Minesweeper(self.level)  # Calculate dimensions
        # self.board.random_safe_reveal()
        _, self.probability = self.board.solve_minefield()
        self.cell_size = 56
        self.rect_size = int(self.cell_size)
        self.line_width = 1
        vlines = self.board.n_cols + 1
        hlines = self.board.n_rows + 1
        self.width = (self.cell_size * self.board.n_cols) + (vlines * self.line_width)
        self.height = (self.cell_size * self.board.n_rows) + (hlines * self.line_width)

        # Define colors
        self.mine_color = (255, 0, 0)  # Red for mines
        self.uncovered_color = (0, 0, 0)  # Black for uncovered cells
        self.covered_color = (50, 50, 50)  # Light grey for covered cells
        self.text_color = (220, 220, 220)  # White text
        self.line_color = (30, 30, 30)  # White color for lines

        self.best_move = None

        self.running = True
        self.fps = 240

        pg.init()
        pg.font.init()
        # self.font = pg.font.Font(None, 18)  # Default font in PyGBag

        self.font = pg.font.SysFont("dseg7classicregular", 16)
        self.clock = pg.time.Clock()
        self.screen = pg.display.set_mode((self.width, self.height))
        pg.display.set_caption("Minesweeper")

        self.key_event_handlers = {
            pg.locals.K_ESCAPE: self.quit,
        }

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
        if key == pg.K_r:  # Check if 'R' key is pressed
            self.reset_game()

        if key == pg.K_0:
            self.level = levels[0]
            self.reset_game()
        if key == pg.K_1:
            self.level = levels[1]
            self.reset_game()

        if key == pg.K_2:
            self.level = levels[2]
            self.reset_game()

        if key == pg.K_3:
            self.level = levels[3]
            self.reset_game()

        else:
            handler = self.key_event_handlers.get(key)
            if handler:
                handler()

    def handle_mouse_event(self, event):

        if not self.board.game_over or self.board.game_won:

            col = (event.pos[0] - self.line_width) // (self.cell_size + self.line_width)
            row = (event.pos[1] - self.line_width) // (self.cell_size + self.line_width)

            # Check if the click is within the bounds of the board
            if 0 <= row < self.board.n_rows and 0 <= col < self.board.n_cols:
                if event.type == pg.MOUSEBUTTONDOWN:
                    if event.button == pg.BUTTON_LEFT:  # Left click
                        self.board.reveal(row, col)

        if not (self.board.game_over or self.board.game_won):
            _, self.probability = self.board.solve_minefield()

    def draw(self):
        self.screen.fill([0, 0, 0])  # Background color
        self.draw_cells()
        self.draw_lines()
        # Check for game over or won condition
        if self.board.game_won or self.board.game_over:
            # Create a transparent overlay surface
            overlay = pygame.Surface(self.screen.get_size(), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 128))  # Semi-transparent black background
            self.screen.blit(overlay, (0, 0))

            # Render main message
            font_size = min(self.width // 15, self.height // 15)  # Dynamic font size
            font = pygame.font.Font(None, font_size)

            if self.board.game_over:
                main_text = "Game Over, Press 'R' to Restart"
            else:
                main_text = "Game Won, Press 'R' to Restart"

            main_text_surface = font.render(
                main_text, True, (255, 255, 255)
            )  # White text
            main_text_rect = main_text_surface.get_rect(
                center=(self.width // 2, self.height // 3)
            )

            # Render current level and difficulty options
            sub_font_size = font_size
            sub_font = pygame.font.Font(None, sub_font_size)

            level_text = (
                f"Current Level: {self.level.capitalize()}"  # Capitalize level string
            )
            level_surface = sub_font.render(level_text, True, (255, 255, 255))
            level_rect = level_surface.get_rect(
                center=(self.width // 2, self.height // 2)
            )

            options_text = "Press 1 - Easy, 2 - Intermediate, 3 - Hard"
            options_surface = sub_font.render(options_text, True, (255, 255, 255))
            options_rect = options_surface.get_rect(
                center=(self.width // 2, (2 * self.height) // 3)
            )

            # Draw everything
            self.screen.blit(main_text_surface, main_text_rect)
            self.screen.blit(level_surface, level_rect)
            self.screen.blit(options_surface, options_rect)

    def draw_cells(self):
        # Other parameters
        corner_radius = self.cell_size // 5  # self.cell_size // 10
        offset = 5  # Small offset to create a black border

        # Draw the cells
        for row in range(self.board.n_rows):
            for col in range(self.board.n_cols):
                x = col * (self.cell_size + self.line_width) + self.line_width
                y = row * (self.cell_size + self.line_width) + self.line_width
                cell = self.board.minefield[row][col]

                # Adjust dimensions to include the offset
                rect_x, rect_y = x + offset, y + offset
                rect_size = self.cell_size - (2 * offset)

                if cell["state"] == self.board.states.UNCOVERED.value:
                    if cell["mine_count"] == -1:
                        pg.draw.rect(
                            self.screen,
                            self.mine_color,
                            (rect_x, rect_y, rect_size, rect_size),
                            border_radius=corner_radius,
                        )
                    else:
                        pg.draw.rect(
                            self.screen,
                            self.uncovered_color,
                            (rect_x, rect_y, rect_size, rect_size),
                            border_radius=corner_radius,
                        )
                        if cell["mine_count"] > 0:
                            text_surface = self.font.render(
                                f"{cell['mine_count']}", True, self.text_color
                            )
                            text_rect = text_surface.get_rect(
                                center=(
                                    rect_x + rect_size // 2,
                                    rect_y + rect_size // 2,
                                )
                            )
                            self.screen.blit(text_surface, text_rect)

                else:
                    if self.probability is not None:
                        if self.probability[row][col] == 0:
                            pg.draw.rect(
                                self.screen,
                                pg.Color("green"),
                                (rect_x, rect_y, rect_size, rect_size),
                                border_radius=corner_radius,
                            )
                        elif self.probability[row][col] == 1:
                            pg.draw.rect(
                                self.screen,
                                pg.Color("red"),
                                (rect_x, rect_y, rect_size, rect_size),
                                border_radius=corner_radius,
                            )
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
                                colormap.get_rgb(self.probability[row][col]),
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
