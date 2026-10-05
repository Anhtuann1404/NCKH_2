"""Check supplied split/group assignments; never infer eTLD+1 with heuristics."""

from dataclasses import dataclass
from typing import Mapping


@dataclass(frozen=True)
class RunPlan:
    variant: str
    seed: int
    train_ids: tuple[str, ...]
    validation_ids: tuple[str, ...]
    test_ids: tuple[str, ...]

    def validate(self, group_by_sample: Mapping[str, str], excluded_ids: frozenset[str] = frozenset()):
        if self.variant not in {'M0', 'M1', 'M2', 'M3', 'B-rule'}:
            raise ValueError('Unknown experiment variant')
        partitions = (self.train_ids, self.validation_ids, self.test_ids)
        if any(not ids or len(ids) != len(set(ids)) for ids in partitions):
            raise ValueError('Each partition must be nonempty and contain unique sample IDs')
        all_ids = [sample for ids in partitions for sample in ids]
        if len(all_ids) != len(set(all_ids)):
            raise ValueError('Sample overlap across train/validation/test')
        if excluded_ids.intersection(all_ids):
            raise ValueError('Pilot/reserved samples entered the run plan')
        if any(sample not in group_by_sample or not group_by_sample[sample] for sample in all_ids):
            raise ValueError('Every sample needs a provided, nonempty group ID')
        groups = [{group_by_sample[sample] for sample in ids} for ids in partitions]
        if any(groups[left] & groups[right] for left, right in ((0, 1), (0, 2), (1, 2))):
            raise ValueError('Group overlap across train/validation/test')
        return {'samples': [len(ids) for ids in partitions], 'groups': [len(group) for group in groups]}
