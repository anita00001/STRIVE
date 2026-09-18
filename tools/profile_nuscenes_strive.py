"""
Profile the STRIVE-specific nuScenes dataset representation.

Outputs:
    metadata/data/nuscenes_strive_statistics.json

Statistics to compute:
    - source scene counts
    - sequence counts by split
    - agent counts by category
    - agents per scene
    - Boston/Singapore counts
    - filtering attrition where recoverable
    - missing-history/future statistics

Important:
    This script must use the same STRIVE dataset preprocessing code
    as training wherever possible rather than independently reimplementing
    the preprocessing rules.
"""