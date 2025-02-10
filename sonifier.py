from random import randint

import mido

from liquiprism import Face, FacePosition, Liquiprism

MIDI_PORT = "IAC Driver Bus 1"


class Sonifier:
    def __init__(self, liquiprism: Liquiprism, midi_port=MIDI_PORT):
        self.liquiprism = liquiprism
        self.midi_out = mido.open_output(midi_port)
        self.note_threshold = 5
        self.pitch_grids = self.create_pitch_grids()

    def create_pitch_grids(self) -> dict[FacePosition, list[list[int]]]:
        pitch_grids = {}
        base_pitches = {
            FacePosition.BOTTOM: 24,
            FacePosition.TOP: 84,
            FacePosition.FRONT: 48,
            FacePosition.BACK: 60,
            FacePosition.LEFT: 36,
            FacePosition.RIGHT: 72,
        }

        major_scale_intervals = [0, 2, 4, 5, 7, 9, 11]
        major_scale_notes = len(major_scale_intervals)

        for face_position, base_pitch in base_pitches.items():
            pitch_grid = []
            for row in range(major_scale_notes):
                scale_base = base_pitch + (major_scale_notes - 1 - row)
                row_pitches = [
                    scale_base + major_scale_intervals[col % major_scale_notes]
                    for col in range(major_scale_notes)
                ]
                pitch_grid.append(row_pitches)
            pitch_grids[face_position] = pitch_grid

        return pitch_grids

    def update(self) -> None:
        for face_position in FacePosition:
            face = self.liquiprism.get_face(face_position)
            midi_channel = face_position.value
            self.sonify_face(
                face, midi_channel, self.pitch_grids[face_position]
            )

    def sonify_face(
        self, face: Face, midi_channel: int, pitch_grid: list[list[int]]
    ) -> None:
        played_pitches = 0
        for i in range(self.liquiprism.size):
            for j in range(self.liquiprism.size):
                cell = face.get_cell((i, j))
                if cell.stimulated and played_pitches <= self.note_threshold:
                    pitch = pitch_grid[i][j]
                    self.play_note_on(midi_channel, pitch)
                    played_pitches += 1
                else:
                    pitch = pitch_grid[i][j]
                    self.play_note_off(midi_channel, pitch)

    def play_note_on(self, channel: int, pitch: int) -> None:
        msg = mido.Message(
            "note_on",
            channel=channel,
            note=pitch,
            velocity=randint(20, 80),
            time=0,
        )
        self.midi_out.send(msg)

    def play_note_off(self, channel: int, pitch: int) -> None:
        msg = mido.Message(
            "note_off",
            channel=channel,
            note=pitch,
            velocity=randint(20, 80),
            time=0,
        )
        self.midi_out.send(msg)
