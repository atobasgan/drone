import enum
class ReliabilityPolicy(enum.Enum): BEST_EFFORT=1; RELIABLE=2
class DurabilityPolicy(enum.Enum): TRANSIENT_LOCAL=1; VOLATILE=2
class HistoryPolicy(enum.Enum): KEEP_LAST=1
class QoSProfile:
    def __init__(self, **kw): self.__dict__.update(kw)
