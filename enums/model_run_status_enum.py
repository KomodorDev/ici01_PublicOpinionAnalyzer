from enum import Enum


class ModelRunStatusEnum(str, Enum):
    PENDING = "pending"        # not started for this model
    RUNNING = "running"        # currently classifying
    DONE = "done"              # finished successfully
    ERROR = "error"            # failed
