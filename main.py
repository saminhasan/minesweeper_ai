import pygame as pg
import pygame.locals
from game_engine import Minesweeper
import numpy as np
import asyncio


class GUI:
    def __init__(self, level: str):
        self.level = level  # Store the level for resetting the game
        self.board = Minesweeper(self.level)  # Calculate dimensions
        # self.board.random_safe_reveal()
        _, self.probability = self.board.solve_minefield()
        self.cell_size = 64
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
        self.flagged_color = (10, 10, 10)  # Dark grey for flagged cells
        self.text_color = (220, 220, 220)  # White text
        self.line_color = (30, 30, 30)  # White color for lines

        self.best_move = None

        self.running = True
        self.fps = 240

        pg.init()
        pg.font.init()
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
                    if event.button == 1:  # Left click
                        self.board.reveal(row, col)
                    elif event.button == 3:  # Right click
                        cell_state = self.board.minefield[row, col]["state"]
                        if cell_state == self.board.states.COVERED.value:
                            self.board.flag(row, col)
                        elif cell_state == self.board.states.FLAGGED.value:
                            self.board.unflag(row, col)
        if not (self.board.game_over or self.board.game_won):
            sol, self.probability = self.board.solve_minefield()
            # self.probability = self.board.predict_model()
            # print(self.probability)
            # print(self.board.convert_minefield())

    def draw(self):
        self.screen.fill([0, 0, 0])  # Background color

        # Other parameters
        gap_size = self.cell_size // 8
        corner_radius = self.cell_size // 5  # self.cell_size // 10
        offset = 5  # Small offset to create a black border

        # Draw the cells
        for row in range(self.board.n_rows):
            for col in range(self.board.n_cols):
                x = col * (self.cell_size + self.line_width) + self.line_width
                y = row * (self.cell_size + self.line_width) + self.line_width
                cell = self.board.minefield[row, col]

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
                elif cell["state"] == self.board.states.FLAGGED.value:
                    pg.draw.rect(
                        self.screen,
                        self.flagged_color,
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
                    if self.probability is not None:
                        if self.probability[row, col] > 0:
                            text_surface = self.font.render(
                                f"{self.probability[row, col]:.2f}",
                                True,
                                self.text_color,
                            )
                            text_rect = text_surface.get_rect(
                                center=(
                                    rect_x + rect_size // 2,
                                    rect_y + rect_size // 2,
                                )
                            )
                        elif self.probability[row, col] == 0:
                            text_surface = self.font.render(f"{0}", True, (0, 255, 0))
                            text_rect = text_surface.get_rect(
                                center=(
                                    rect_x + rect_size // 2,
                                    rect_y + rect_size // 2,
                                )
                            )
                        self.screen.blit(text_surface, text_rect)

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
        # Reinitialize the Minesweeper board
        self.board = Minesweeper(self.level)
        _, self.probability = self.board.solve_minefield()


async def main():
    game = GUI("easy")

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
