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


@dataclass
class FilledFrame:
    frame: Frame
    lines: List[Tuple[FrameCoord, FrameCoord]]

    def add_line(self, start_pos: FrameCoord, end_pos: FrameCoord):
        self.lines.append((start_pos, end_pos))


@dataclass
class MathCoord:
    # both should be between -1 and 1
    x: float
    y: float

    # frame angle is in multiples of pi/2
    def rotated(self, frame_angle):
        x, y = self.x, self.y
        sin = math.sin(math.pi * frame_angle / 2)
        cos = math.cos(math.pi * frame_angle / 2)
        u = x * cos + y * sin
        v = x * (-sin) + y * cos

        return MathCoord(u, v)

    def to_frame_coordinate(self):
        x = (self.x + 1) / 2
        y = 1 - (self.y + 1) / 2
        return (x, y)


def pseudo_hilbert_curve(frame, order) -> FilledFrame:
    if order > 1:
        smaller_frames = frame.hilbert_split()
        tr = pseudo_hilbert_curve(smaller_frames[0], order - 1)
        tl = pseudo_hilbert_curve(smaller_frames[1], order - 1)
        br = pseudo_hilbert_curve(smaller_frames[2], order - 1).rotate(1)
        bl = pseudo_hilbert_curve(smaller_frames[3], order - 1).rotate(-1)

        return FilledFrame.compose(frame, (bl, tl, tr, br))

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
