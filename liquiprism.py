from enum import Enum

import numpy as np


class RelativeFacePosition(Enum):
    TOP = 0
    BOTTOM = 1
    LEFT = 2
    RIGHT = 3


class FacePosition(Enum):
    FRONT = 0
    BACK = 1
    LEFT = 2
    RIGHT = 3
    TOP = 4
    BOTTOM = 5


class Cell:
    def __init__(self, face: "Face", position: tuple[int], is_alive: bool):
        self.face = face
        self.position = position
        self.is_alive = is_alive
        self.will_be_alive = None
        self.stimulated = False

    def __repr__(self):
        return f"Cell(face={self.face.position}, position={self.position}, is_alive={self.is_alive})"

    def is_cell_on_face_edge(self) -> bool:
        i, j = self.position
        return (
            i == 0
            or i == self.face.size - 1
            or j == 0
            or j == self.face.size - 1
        )


class Face:
    def __init__(
        self, position: FacePosition, size: int, update_rate: int = 1
    ):
        self.position = position
        self.size = size
        self.cells = self._initialize_cells()
        self.update_rate = update_rate

    def __repr__(self):
        return f"Face(position={self.position})"

    def _initialize_cells(self) -> list[Cell]:
        return [
            Cell(
                face=self,
                position=(i, j),
                is_alive=np.random.choice([True, False], p=[0.5, 0.5]),
            )
            for i in range(self.size)
            for j in range(self.size)
        ]

    def get_cell(self, position: tuple[int]) -> Cell:
        return self.cells[position[0] * self.size + position[1]]


class Liquiprism:
    def __init__(self, size: int, random_update_rate: bool = False):
        self.size = size
        self.faces = [
            Face(
                position=position,
                size=size,
                update_rate=(
                    1 if not random_update_rate else np.random.randint(1, 4)
                ),
            )
            for position in list(FacePosition)
        ]
        self.face_map = self._initialize_face_map()
        self.activity = 0  # counter for number of cells that were stimulated in the last step
        self.CELL_STATE_CHANGE_THRESHOLD = self.size**2
        self.step_counter = 0
        self.frontmost_face = self.faces[0]

    def _initialize_face_map(self) -> dict[FacePosition, dict[str, Face]]:
        return {
            FacePosition.FRONT: {
                RelativeFacePosition.TOP: FacePosition.TOP,
                RelativeFacePosition.BOTTOM: FacePosition.BOTTOM,
                RelativeFacePosition.LEFT: FacePosition.LEFT,
                RelativeFacePosition.RIGHT: FacePosition.RIGHT,
            },
            FacePosition.BACK: {
                RelativeFacePosition.TOP: FacePosition.TOP,
                RelativeFacePosition.BOTTOM: FacePosition.BOTTOM,
                RelativeFacePosition.LEFT: FacePosition.RIGHT,
                RelativeFacePosition.RIGHT: FacePosition.LEFT,
            },
            FacePosition.LEFT: {
                RelativeFacePosition.TOP: FacePosition.TOP,
                RelativeFacePosition.BOTTOM: FacePosition.BOTTOM,
                RelativeFacePosition.LEFT: FacePosition.BACK,
                RelativeFacePosition.RIGHT: FacePosition.FRONT,
            },
            FacePosition.RIGHT: {
                RelativeFacePosition.TOP: FacePosition.TOP,
                RelativeFacePosition.BOTTOM: FacePosition.BOTTOM,
                RelativeFacePosition.LEFT: FacePosition.FRONT,
                RelativeFacePosition.RIGHT: FacePosition.BACK,
            },
            FacePosition.TOP: {
                RelativeFacePosition.TOP: FacePosition.BACK,
                RelativeFacePosition.BOTTOM: FacePosition.FRONT,
                RelativeFacePosition.LEFT: FacePosition.LEFT,
                RelativeFacePosition.RIGHT: FacePosition.RIGHT,
            },
            FacePosition.BOTTOM: {
                RelativeFacePosition.TOP: FacePosition.FRONT,
                RelativeFacePosition.BOTTOM: FacePosition.BACK,
                RelativeFacePosition.LEFT: FacePosition.LEFT,
                RelativeFacePosition.RIGHT: FacePosition.RIGHT,
            },
        }

    def get_face(self, face_position: FacePosition) -> Face:
        return next(
            face for face in self.faces if face.position == face_position
        )

    def get_cell_neighbors(self, face: Face, cell: Cell) -> list[Cell]:
        i, j = cell.position
        neighbors = []

        for i_offset in [-1, 0, 1]:
            for j_offset in [-1, 0, 1]:
                if i_offset == 0 and j_offset == 0:
                    continue
                ni, nj = i + i_offset, j + j_offset
                if 0 <= ni < face.size and 0 <= nj < face.size:
                    neighbors.append(face.get_cell((ni, nj)))
                else:
                    neighbors.extend(
                        self.get_adjacent_face_cell_neighbors(
                            face, cell, i_offset, j_offset
                        )
                    )

        return neighbors

    def get_bellow_cell_neighbor(self, face: Face, cell: Cell) -> Cell:
        i, j = cell.position
        if i == face.size - 1:
            neighbor_face = self.get_face(
                self.face_map[face.position][RelativeFacePosition.BOTTOM]
            )
            return neighbor_face.get_cell((0, j))

        return face.get_cell((i + 1, j))

    def get_adjacent_face_cell_neighbors(
        self, face: Face, cell: Cell, i_offset: int, j_offset: int
    ) -> list[Cell]:
        neighbors = []

        i, j = cell.position
        ni, nj = i + i_offset, j + j_offset

        neighbor_face = face
        n_neighbor_faces = 0

        if ni < 0:
            neighbor_face = self.get_face(
                self.face_map[face.position][RelativeFacePosition.TOP]
            )
            ni = face.size - 1
            n_neighbor_faces += 1
        elif ni >= face.size:
            neighbor_face = self.get_face(
                self.face_map[face.position][RelativeFacePosition.BOTTOM]
            )
            ni = 0
            n_neighbor_faces += 1

        if nj < 0:
            neighbor_face = self.get_face(
                self.face_map[face.position][RelativeFacePosition.LEFT]
            )
            nj = face.size - 1
            n_neighbor_faces += 1
        elif nj >= face.size:
            neighbor_face = self.get_face(
                self.face_map[face.position][RelativeFacePosition.RIGHT]
            )
            nj = 0
            n_neighbor_faces += 1

        if n_neighbor_faces == 1:
            neighbors.append(neighbor_face.get_cell((ni, nj)))

        return neighbors

    def step(self) -> None:
        self.activity = 0

        for face in self.faces:
            if self.step_counter % face.update_rate == 0:
                for cell in face.cells:
                    self._apply_rules(face, cell)

        for face in self.faces:
            if self.step_counter % face.update_rate == 0:
                for cell in face.cells:
                    cell.is_alive = cell.will_be_alive
                    cell.will_be_alive = None

        self.step_counter += 1

    def _apply_rules(self, face: Face, cell: Cell) -> None:
        if self.frontmost_face == face:
            cell.will_be_alive = self._apply_stimulus_rule(cell)
        else:
            neighbors = self.get_cell_neighbors(face, cell)
            alive_neighbors = sum(
                1 for neighbor in neighbors if neighbor.is_alive
            )

            if self.activity < self.CELL_STATE_CHANGE_THRESHOLD:
                cell.will_be_alive = self._apply_stochastic_rule(
                    cell, alive_neighbors
                )
            else:
                cell.will_be_alive = self._apply_conventional_rule(
                    cell, alive_neighbors
                )

        cell.stimulated = cell.will_be_alive and not cell.is_alive
        if cell.stimulated:
            self.activity += 1

    def _apply_conventional_rule(
        self, cell: Cell, alive_neighbors: int
    ) -> bool:
        if cell.is_alive:
            return alive_neighbors in [2, 3]

        return alive_neighbors >= 4

    def _apply_stochastic_rule(self, cell: Cell, alive_neighbors: int) -> bool:
        if cell.is_alive:
            return alive_neighbors in [2, 3]

        bellow_neighbor = self.get_bellow_cell_neighbor(cell.face, cell)

        return bellow_neighbor.is_alive and np.random.choice(
            [True, False], p=[1 / 3, 2 / 3]
        )

    def _apply_stimulus_rule(
        self, cell: Cell, activation_probability: int = 0.2
    ) -> bool:
        return cell.is_alive or np.random.choice(
            [True, False],
            p=[activation_probability, 1 - activation_probability],
        )
