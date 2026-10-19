from .time import Time
WORLD = {'t': 0, 'topics': {}, 'timers': [], 'log': []}

class _P:
    def __init__(self, v): self.value = v
class _Pub:
    def __init__(self, topic): self.topic = topic
    def publish(self, m):
        for cb in WORLD['topics'].setdefault(self.topic, []): cb(m)
class _Timer:
    def __init__(self, period, cb): self.period, self.cb, self.next, self.on = period, cb, 0, True
    def cancel(self): self.on = False
class _Log:
    def __init__(self, n): self.n = n
    def _w(self, lvl, m): WORLD['log'].append((WORLD['t'], lvl, m)); print(f'{WORLD["t"]/1e9:7.2f} [{lvl}] {m}')
    def info(self, m): self._w('I', m)
    def warn(self, m): self._w('W', m)
    def debug(self, m): pass
class _Clock:
    def now(self): return Time(WORLD['t'])
class Node:
    def __init__(self, name): self._n = name; self._params = WORLD.get('params', {})
    def declare_parameter(self, n, d): return _P(self._params.get(n, d))
    def create_publisher(self, t, topic, q): return _Pub(topic)
    def create_subscription(self, t, topic, cb, q, callback_group=None):
        WORLD['topics'].setdefault(topic, []).append(cb); return object()
    def create_timer(self, p, cb, callback_group=None):
        t = _Timer(p, cb); WORLD['timers'].append(t); return t
    def get_logger(self): return _Log(self._n)
    def get_clock(self): return _Clock()
    def get_topic_names_and_types(self):
        return [(t, []) for t in WORLD.get('px4_out', [])]
    def destroy_node(self): pass
