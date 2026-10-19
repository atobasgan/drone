class Time:
    def __init__(self, nanoseconds=0): self.nanoseconds = nanoseconds
    def __sub__(self, o): return Time(self.nanoseconds - o.nanoseconds)
    def to_msg(self):
        from builtin_interfaces.msg import Time as T
        return T(sec=self.nanoseconds // 10**9, nanosec=self.nanoseconds % 10**9)
    @staticmethod
    def from_msg(m): return Time(m.sec * 10**9 + m.nanosec)
