"""GB1 four-site mutation parsing and 56-residue domain reconstruction."""
from __future__ import annotations

from dataclasses import dataclass
import re
from typing import Iterable

AMINO_ACIDS = "ACDEFGHIKLMNPQRSTVWY"
GB1_WT_SEQUENCE = "MQYKLILNGKTLKGETTTEAVDAATAEKVFKQYANDNGVDGEWTYDDATKTFTVTE"
MUTABLE_POSITIONS = (39, 40, 41, 54)
WT_VARIANT = "VDGV"
_MUTATION = re.compile(r"^([ACDEFGHIKLMNPQRSTVWY])(39|40|41|54)([ACDEFGHIKLMNPQRSTVWY])$")


@dataclass(frozen=True, slots=True)
class Mutation:
    wild_type: str
    position: int
    mutant: str

    def __str__(self) -> str:
        return f"{self.wild_type}{self.position}{self.mutant}"


def parse_mutation(text: str) -> Mutation:
    """Parse and validate notation such as ``V39I`` against the GB1 WT."""
    match = _MUTATION.fullmatch(text.strip().upper())
    if match is None:
        raise ValueError(f"invalid GB1 mutation {text!r}; expected e.g. V39I at one of {MUTABLE_POSITIONS}")
    wild_type, position_text, mutant = match.groups()
    position = int(position_text)
    expected = GB1_WT_SEQUENCE[position - 1]
    if wild_type != expected:
        raise ValueError(f"wild-type residue mismatch at {position}: got {wild_type}, expected {expected}")
    return Mutation(wild_type, position, mutant)


def validate_variant(variant: str) -> str:
    """Return a normalized four-residue GB1 variant or raise ``ValueError``."""
    normalized = variant.strip().upper()
    if len(normalized) != len(MUTABLE_POSITIONS) or any(aa not in AMINO_ACIDS for aa in normalized):
        raise ValueError("variant must contain exactly four standard amino acids (positions 39,40,41,54)")
    return normalized


def variant_to_mutations(variant: str, *, include_synonymous: bool = False) -> tuple[Mutation, ...]:
    normalized = validate_variant(variant)
    mutations = tuple(
        Mutation(wt, position, mutant)
        for wt, position, mutant in zip(WT_VARIANT, MUTABLE_POSITIONS, normalized)
        if include_synonymous or wt != mutant
    )
    return mutations


def apply_mutations(mutations: Iterable[str | Mutation]) -> str:
    """Apply validated mutations to the canonical 56-aa GB1 domain sequence."""
    sequence = list(GB1_WT_SEQUENCE)
    seen: set[int] = set()
    for item in mutations:
        mutation = parse_mutation(item) if isinstance(item, str) else item
        if mutation.position not in MUTABLE_POSITIONS:
            raise ValueError(f"position {mutation.position} is outside the GB1 four-site landscape")
        if mutation.position in seen:
            raise ValueError(f"duplicate mutation at position {mutation.position}")
        if mutation.wild_type != GB1_WT_SEQUENCE[mutation.position - 1]:
            raise ValueError(f"wild-type residue mismatch at {mutation.position}")
        if mutation.mutant not in AMINO_ACIDS:
            raise ValueError(f"non-standard or stop residue {mutation.mutant!r}")
        sequence[mutation.position - 1] = mutation.mutant
        seen.add(mutation.position)
    return "".join(sequence)


def variant_to_sequence(variant: str) -> str:
    return apply_mutations(variant_to_mutations(variant))


def sequence_to_variant(sequence: str) -> str:
    normalized = sequence.strip().upper()
    if len(normalized) != len(GB1_WT_SEQUENCE):
        raise ValueError(f"GB1 domain sequence must be {len(GB1_WT_SEQUENCE)} residues")
    if any(aa not in AMINO_ACIDS for aa in normalized):
        raise ValueError("sequence contains a non-standard or stop residue")
    mutable = set(MUTABLE_POSITIONS)
    mismatches = [i for i, (actual, expected) in enumerate(zip(normalized, GB1_WT_SEQUENCE), start=1)
                  if actual != expected and i not in mutable]
    if mismatches:
        raise ValueError(f"sequence changes immutable GB1 position(s): {mismatches}")
    return "".join(normalized[position - 1] for position in MUTABLE_POSITIONS)
