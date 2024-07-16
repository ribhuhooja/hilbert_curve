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
        pass


@dataclass
class FilledFrame:
    frame: Frame
    lines: List[Tuple[FrameCoord, FrameCoord]]

    def add_line(self, start_pos: FrameCoord, end_pos: FrameCoord):
        self.lines.append((start_pos, end_pos))

    def rotate(self, angle_factor: int) -> Self:
        angle = angle_factor * math.pi / 2
        map(lambda line: (line[0].rotated(angle), line[1].rotated(angle)), self.lines)
        return self

    def subsume(self, other: "FilledFrame"):
        for line in other.lines:
            start_pos, end_pos = line
            new_start_pos = self.frame.frame_coords_of(
                other.frame.real_coords(start_pos)
            )
            new_end_pos = self.frame.frame_coords_of(other.frame.real_coords(end_pos))
            self.add_line(new_start_pos, new_end_pos)


def pseudo_hilbert_curve(frame, order) -> FilledFrame:
    if order > 1:
        smaller_frames = frame.hilbert_split()
        tr = pseudo_hilbert_curve(smaller_frames[0], order - 1)
        tl = pseudo_hilbert_curve(smaller_frames[1], order - 1)
        br = pseudo_hilbert_curve(smaller_frames[2], order - 1).rotate(1)
        bl = pseudo_hilbert_curve(smaller_frames[3], order - 1).rotate(-1)

        result = FilledFrame(frame, [])
        result.subsume(bl)
        result.subsume(tl)
        result.subsume(tr)
        result.subsume(br)

        return result

    else:
        to_ret = FilledFrame(frame, [])
        to_ret.add_line(FrameCoord(0.25, 0.75), FrameCoord(0.25, 0.25))
        to_ret.add_line(FrameCoord(0.25, 0.25), FrameCoord(0.75, 0.25))
        to_ret.add_line(FrameCoord(0.75, 0.25), FrameCoord(0.75, 0.75))

        return to_ret


def render(screen, frame, t):
    for line in frame.lines:
        start_pos = int(line[0].x), int(line[0].y)
        end_pos = int(line[1].x), int(line[1].y)
        pygame.draw.line(screen, (255, 255, 255), start_pos, end_pos)
    pygame.display.update()


def mainLoop():
    exit = False
    clock = pygame.time.Clock()
    screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
    t = 0

    frame = Frame(Vec2Int(0, 0), Vec2Int(WINDOW_WIDTH, WINDOW_HEIGHT))
    to_render = pseudo_hilbert_curve(frame, 3)

    while not exit:
        t += clock.tick(FPS)
        render(screen, to_render, t)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                exit = True
                break


if __name__ == "__main__":
    pygame.init()
    pygame.display.set_caption("Hilbert")
    mainLoop()
    pygame.quit()
