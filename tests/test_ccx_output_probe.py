from __future__ import annotations

import struct
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import wo03_ccx_output_probe as probe


class OutputProbeFormatTests(unittest.TestCase):
    def test_output_card_insertion_changes_only_requested_output(self) -> None:
        source = "*HEADING\nA\n*STEP\n*HEAT TRANSFER,STEADY STATE\n*END STEP\n"
        result = probe.add_output_request(source)
        self.assertEqual(result.replace("*NODE OUTPUT\nNT,RFL\n", "", 1), source)

    def test_decode_scalar_binary_frd_records_and_terminator(self) -> None:
        values = [(1, 308.15), (2, 573.15)]
        records = b"".join(struct.pack("<if", node, value) for node, value in values)
        frd = b" -4  NDTEMP 1 1\n -5  T 1 1 0 0\n" + records + b"    1PSTEP 2\n"
        decoded = probe.parse_binary_scalar_field(frd, b"NDTEMP", [1, 2])
        self.assertEqual(list(decoded), [1, 2])
        self.assertAlmostEqual(decoded[1], 308.15, places=4)
        self.assertAlmostEqual(decoded[2], 573.15, places=4)

    def test_float32_spacing_is_reported_at_single_precision(self) -> None:
        self.assertAlmostEqual(probe.float32_spacing(300.0), 2**-15)

    def test_rejects_wrong_ids_nonfinite_and_truncated_records(self) -> None:
        header = b" -4  NDTEMP 1 1\n -5  T 1 1 0 0\n"
        footer = b"    1PSTEP 2\n"
        # Independent IEEE-754 bytes: ID=1, float32 1.0, then infinity.
        valid = bytes.fromhex("01000000 0000803f")
        self.assertEqual(
            probe.parse_binary_scalar_field(header + valid + footer, b"NDTEMP", [1]),
            {1: 1.0},
        )
        corrupt = [
            bytes.fromhex("02000000 0000803f"),
            bytes.fromhex("01000000 0000807f"),
            valid[:-1],
        ]
        for record in corrupt:
            with self.subTest(record=record), self.assertRaises(ValueError):
                probe.parse_binary_scalar_field(header + record + footer, b"NDTEMP", [1])


if __name__ == "__main__":
    unittest.main()
