import pygame
from dataclasses import dataclass
from typing import Tuple, List, Self
import math

WINDOW_WIDTH = 800
WINDOW_HEIGHT = 800
FPS = 60


@dataclass
class Vec2:
    x: float
    y: float

    def to_int(self):
        return Vec2Int(int(self.x), int(self.y))

    def __add__(self, other):
        return Vec2Int(self.x + other.x, self.y + other.y)

    def __truediv__(self, num):
        return Vec2Int(self.x // num, self.y // num)

    def destructure(self):
        return (self.x, self.y)


@dataclass
class Vec2Int:
    x: int
    y: int

    def to_vec2(self):
        return Vec2(self.x, self.y)

    def __add__(self, other):
        return Vec2Int(self.x + other.x, self.y + other.y)

    def __truediv__(self, num):
        return Vec2Int(self.x // num, self.y // num)

    def destructure(self):
        return (self.x, self.y)


# bounded in [0,1]
@dataclass
class FrameCoord:
    x: float
    y: float

    def rotated(self, angle: float) -> "FrameCoord":
        math_x = 2 * self.x - 1
        math_y = 1 - 2 * self.y
        sin = math.sin(angle)
        cos = math.cos(angle)

        u = math_x * cos + math_y * sin
        v = math_x * (-sin) + math_y * cos
        x = (u + 1) / 2
        y = 1 - (v + 1) / 2
        return FrameCoord(x, y)


@dataclass
class Frame:
    top_left: Vec2Int
    bottom_right: Vec2Int

    # returns four frames according to how
    # hilbert curves are constructed
    def hilbert_split(self) -> Tuple["Frame", "Frame", "Frame", "Frame"]:
        left_x, top_y = self.top_left.destructure()
        right_x, bottom_y = self.bottom_right.destructure()
        mid_x, mid_y = ((self.top_left + self.bottom_right) / 2).destructure()
        midpoint = Vec2Int(mid_x, mid_y)

        tl_frame = Frame(self.top_left, midpoint)
        tr_frame = Frame(Vec2Int(mid_x, top_y), Vec2Int(right_x, mid_y))
        bl_frame = Frame(Vec2Int(left_x, mid_y), Vec2Int(mid_x, bottom_y))

        br_frame = Frame(midpoint, self.bottom_right)

        return (bl_frame, tl_frame, tr_frame, br_frame)

    # frame coords should be in [0,1]
    def real_coords(self, frame_coord: FrameCoord) -> Vec2:
        left_x, top_y = self.top_left.destructure()
        right_x, bottom_y = self.bottom_right.destructure()

        x = left_x + frame_coord.x * (right_x - left_x)
        y = top_y + frame_coord.y * (bottom_y - top_y)

        return Vec2(x, y)

    def frame_coords_of(self, real_coords: Vec2) -> FrameCoord:
        left_x, top_y = self.top_left.destructure()
        right_x, bottom_y = self.bottom_right.destructure()
        frame_x = (real_coords.x - left_x) / (right_x - left_x)
        frame_y = (real_coords.y - top_y) / (bottom_y - top_y)
        return FrameCoord(frame_x, frame_y)


@dataclass
class FilledFrame:
    frame: Frame
    lines: List[Tuple[FrameCoord, FrameCoord]]

    def add_line(self, start_pos: FrameCoord, end_pos: FrameCoord):
        self.lines.append((start_pos, end_pos))

    def rotate(self, angle_factor: int) -> Self:
        angle = angle_factor * math.pi / 2
        for i in range(len(self.lines)):
            line = self.lines[i]
            new_start = line[0].rotated(angle)
            new_end = line[1].rotated(angle)
            self.lines[i] = (new_start, new_end)
        return self

    def reorient(self):
        self.lines = self.lines[::-1]
        for i in range(len(self.lines)):
            line = self.lines[i]
            self.lines[i] = (line[1], line[0])
        return self

    def subsume(self, other: "FilledFrame"):
        for line in other.lines:
            start_pos, end_pos = line
            new_start_pos = self.frame.frame_coords_of(
                other.frame.real_coords(start_pos)
            )
            new_end_pos = self.frame.frame_coords_of(other.frame.real_coords(end_pos))
            self.add_line(new_start_pos, new_end_pos)

    def subsume_with_connection(self, other: "FilledFrame"):
        if len(self.lines) == 0:
            self.subsume(other)
            return

        end_pos_of_last_line = self.lines[-1][1]
        start_pos_of_first_line = self.frame.frame_coords_of(
            other.frame.real_coords(other.lines[0][0])
        )
        self.add_line(end_pos_of_last_line, start_pos_of_first_line)
        self.subsume(other)

    def real_coords(self, frame_coords: FrameCoord) -> Vec2:
        return self.frame.real_coords(frame_coords)

    def to_rendering_queue(self) -> "RenderingQueue":
        new_frame = RenderingQueue()
        for line in self.lines:
            start_pos = self.real_coords(line[0]).to_int()
            end_pos = self.real_coords(line[1]).to_int()
            new_frame.lines.append((start_pos, end_pos))

        return new_frame


def pseudo_hilbert_curve(frame, order) -> FilledFrame:
    if order > 1:
        smaller_frames = frame.hilbert_split()
        bl = pseudo_hilbert_curve(smaller_frames[0], order - 1).rotate(1).reorient()
        tl = pseudo_hilbert_curve(smaller_frames[1], order - 1)
        tr = pseudo_hilbert_curve(smaller_frames[2], order - 1)
        br = pseudo_hilbert_curve(smaller_frames[3], order - 1).rotate(-1).reorient()

        result = FilledFrame(frame, [])
        result.subsume(bl)
        result.subsume_with_connection(tl)
        result.subsume_with_connection(tr)
        result.subsume_with_connection(br)

        return result

    else:
        to_ret = FilledFrame(frame, [])
        to_ret.add_line(FrameCoord(0.25, 0.75), FrameCoord(0.25, 0.25))
        to_ret.add_line(FrameCoord(0.25, 0.25), FrameCoord(0.75, 0.25))
        to_ret.add_line(FrameCoord(0.75, 0.25), FrameCoord(0.75, 0.75))

        return to_ret


###################################### GRAPHICS STUFF #########################

PALETTE_START = (255, 0, 0)
PALETTE_END = (0, 255, 0)


@dataclass
class RenderingQueue:
    lines: List[Tuple[Vec2Int, Vec2Int]]
    lines_drawn: int

    def __init__(self) -> None:
        self.lines = []
        self.lines_drawn = 0


def lerp(first, second, frac):
    return first + frac * (second - first)


def lerp_color(
    first: Tuple[int, int, int], second: Tuple[int, int, int], frac
) -> Tuple[int, int, int]:
    r = int(lerp(first[0], second[0], frac))
    g = int(lerp(first[1], second[1], frac))
    b = int(lerp(first[2], second[2], frac))

    return (r, g, b)


def render(screen, frame: RenderingQueue, t):
    total_lines = len(frame.lines)
    lines_drawn = 0
    for line in frame.lines:
        color = lerp_color(PALETTE_START, PALETTE_END, lines_drawn / total_lines)
        start_pos = line[0].destructure()
        end_pos = line[1].destructure()
        pygame.draw.line(screen, color, start_pos, end_pos)
        lines_drawn += 1
    pygame.display.update()


def clear_screen(screen):
    screen.fill((0, 0, 0))


####################################### MAIN LOOP #############################


def mainLoop():
    exit = False
    rendered = False
    clock = pygame.time.Clock()
    screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
    t = 0
    order = 1

    frame = Frame(Vec2Int(0, 0), Vec2Int(WINDOW_WIDTH, WINDOW_HEIGHT))

    while not exit:
        t += clock.tick(FPS)
        if not rendered:
            to_render = pseudo_hilbert_curve(frame, order).to_rendering_queue()
            render(screen, to_render, t)
            rendered = True

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                exit = True
                break
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    clear_screen(screen)
                    order += 1
                    rendered = False


if __name__ == "__main__":
    pygame.init()
    pygame.display.set_caption("Hilbert")
    mainLoop()
    pygame.quit()
