from enum import Enum, auto


class PipelineState(Enum):
    INIT = auto()
    RESOLVING_IDENTITY = auto()
    SEARCHING = auto()
    DOWNLOADING = auto()
    EXTRACTING = auto()
    MATCHING_METADATA = auto()
    TAGGING = auto()
    STORING = auto()
    FINALIZED = auto()
    FAILED = auto()
