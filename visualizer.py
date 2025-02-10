import math

import pygame

from liquiprism import Face, FacePosition, Liquiprism

pygame.init()

WIDTH, HEIGHT = 800, 800
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)


class Visualizer:
    FACE_TINTS = {
        FacePosition.FRONT: (0, 255, 0),
        FacePosition.BACK: (255, 0, 0),
        FacePosition.LEFT: (0, 255, 255),
        FacePosition.RIGHT: (255, 0, 255),
        FacePosition.TOP: (255, 255, 0),
        FacePosition.BOTTOM: (0, 0, 255),
    }

    FACE_VERTICES = {
        FacePosition.FRONT: (3, 2, 1, 0),
        FacePosition.BACK: (6, 7, 4, 5),
        FacePosition.LEFT: (7, 3, 0, 4),
        FacePosition.RIGHT: (2, 6, 5, 1),
        FacePosition.TOP: (7, 6, 2, 3),
        FacePosition.BOTTOM: (0, 1, 5, 4),
    }

    def __init__(self, liquiprism: Liquiprism):
        self.liquiprism = liquiprism
        self.angle_x = 0
        self.angle_y = 0
        self.angle_z = 0
        self.scale = 150
        self.clock = pygame.time.Clock()
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))

        self.vertices = [
            [-1, -1, -1],
            [1, -1, -1],
            [1, 1, -1],
            [-1, 1, -1],
            [-1, -1, 1],
            [1, -1, 1],
            [1, 1, 1],
            [-1, 1, 1],
        ]

    def rotate_x(self, point: tuple[int], angle: float) -> tuple:
        x, y, z = point
        cos_theta = math.cos(angle)
        sin_theta = math.sin(angle)
        y_new = y * cos_theta - z * sin_theta
        z_new = y * sin_theta + z * cos_theta
        return x, y_new, z_new

    def rotate_y(self, point: tuple[int], angle: float) -> tuple:
        x, y, z = point
        cos_theta = math.cos(angle)
        sin_theta = math.sin(angle)
        x_new = x * cos_theta + z * sin_theta
        z_new = -x * sin_theta + z * cos_theta
        return x_new, y, z_new

    def rotate_z(self, point: tuple[int], angle: float) -> tuple:
        x, y, z = point
        cos_theta = math.cos(angle)
        sin_theta = math.sin(angle)
        x_new = x * cos_theta - y * sin_theta
        y_new = x * sin_theta + y * cos_theta
        return x_new, y_new, z

    def project(self, point: tuple[int]):
        x, y, _ = point
        x_proj = x * self.scale + WIDTH // 2
        y_proj = -y * self.scale + HEIGHT // 2
        return int(x_proj), int(y_proj)

    def interpolate(self, v0, v1, v3, v2, t1, t2):
        x0, y0 = self.interpolate_linear(v0, v1, t2)
        x1, y1 = self.interpolate_linear(v3, v2, t2)
        return self.interpolate_linear((x0, y0), (x1, y1), t1)

    def interpolate_linear(self, v0, v1, t):
        x0, y0 = v0
        x1, y1 = v1
        return (x0 * (1 - t) + x1 * t, y0 * (1 - t) + y1 * t)

    def calculate_face_depth(self, face_vertices, vertices):
        return sum(vertices[idx][2] for idx in face_vertices) / len(
            face_vertices
        )

    def draw_face(
        self, face_vertices: list[int], liquiprism_face: Face, vertices, tint
    ):
        points = [vertices[idx] for idx in face_vertices]
        for i in range(self.liquiprism.size):
            for j in range(self.liquiprism.size):
                top_left = self.interpolate(
                    points[0],
                    points[1],
                    points[3],
                    points[2],
                    i / self.liquiprism.size,
                    j / self.liquiprism.size,
                )
                top_right = self.interpolate(
                    points[0],
                    points[1],
                    points[3],
                    points[2],
                    i / self.liquiprism.size,
                    (j + 1) / self.liquiprism.size,
                )
                bottom_left = self.interpolate(
                    points[0],
                    points[1],
                    points[3],
                    points[2],
                    (i + 1) / self.liquiprism.size,
                    j / self.liquiprism.size,
                )
                bottom_right = self.interpolate(
                    points[0],
                    points[1],
                    points[3],
                    points[2],
                    (i + 1) / self.liquiprism.size,
                    (j + 1) / self.liquiprism.size,
                )

                cell = liquiprism_face.get_cell((i, j))
                color = WHITE if cell.is_alive else BLACK
                blended_color = self.blend_color(tint, color)

                pygame.draw.polygon(
                    self.screen,
                    blended_color,
                    [top_left, top_right, bottom_right, bottom_left],
                )
                pygame.draw.lines(
                    self.screen,
                    WHITE,
                    True,
                    [top_left, top_right, bottom_right, bottom_left],
                    1,
                )

    def blend_color(self, base_color, grid_color, blend_factor=0.5):
        return tuple(
            int(
                base_color[i] * blend_factor
                + grid_color[i] * (1 - blend_factor)
            )
            for i in range(3)
        )

    def draw_legend(self):
        font = pygame.font.SysFont("Courier New", 12)
        legend_x = 10
        legend_y = 10
        square_size = 12

        text = font.render("face position  update rate", False, WHITE)
        self.screen.blit(text, (legend_x + square_size + 5, legend_y))
        legend_y += square_size + 10

        for face_position, color in self.FACE_TINTS.items():
            pygame.draw.rect(
                self.screen,
                color,
                (legend_x, legend_y, square_size, square_size),
            )

            face = self.liquiprism.get_face(face_position)
            text = font.render(
                f"{face_position.name.lower():<15}{face.update_rate}",
                False,
                WHITE,
            )
            self.screen.blit(text, (legend_x + square_size + 5, legend_y))

            legend_y += square_size + 10

    def draw_steps(self):
        font = pygame.font.SysFont("Courier New", 12)
        text = font.render(
            f"Step: {self.liquiprism.step_counter}", False, WHITE
        )
        _, steps_y = self.screen.get_size()
        self.screen.blit(text, (10, steps_y - 20))

    def draw_cells_state_change(self):
        font = pygame.font.SysFont("Courier New", 12)
        text = font.render(
            f"Stimulated cells: {self.liquiprism.activity}",
            False,
            WHITE,
        )
        _, steps_y = self.screen.get_size()
        self.screen.blit(text, (10, steps_y - 40))

    def render(self):
        self.draw_legend()
        self.draw_steps()
        self.draw_cells_state_change()

        rotated_vertices = [
            self.rotate_x(
                self.rotate_y(
                    self.rotate_z(vertex, self.angle_z), self.angle_y
                ),
                self.angle_x,
            )
            for vertex in self.vertices
        ]

        transformed_vertices = [self.project(v) for v in rotated_vertices]

        sorted_faces = sorted(
            self.FACE_VERTICES.items(),
            key=lambda item: self.calculate_face_depth(
                item[1], rotated_vertices
            ),
            reverse=True,
        )

        for face_position, face_vertices in sorted_faces:
            liquiprism_face = self.liquiprism.get_face(face_position)
            self.draw_face(
                face_vertices,
                liquiprism_face,
                transformed_vertices,
                self.FACE_TINTS[face_position],
            )

        self.liquiprism.frontmost_face = self.liquiprism.get_face(
            face_position
        )
