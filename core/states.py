from enum import Enum, auto


class PipelineState(Enum):
    INIT = auto()
    SEARCHING_MEDIA = auto()
    RESOLVING_IDENTITY = auto()
    SEARCHING = auto()
    DOWNLOADING = auto()
    EXTRACTING = auto()
    MATCHING_METADATA = auto()
    USER_INTENT_SELECTION = auto()
    USER_METADATA_SELECTION = auto()
    TAGGING = auto()
    STORING = auto()
    FINALIZED = auto()
    ARCHIVING = auto()
    FAILED = auto()
