class ABLoop:
    def __init__(self, engine):
        self.engine = engine
        self.path = None
        self.point_a = None
        self.point_b = None
        self.active = False

    def set_a(self, path, position):
        if not path:
            return False, "A-B loop works with media files"
        if position is None:
            return False, "cannot set A-B loop point"
        self.path = path
        self.point_a = float(position)
        self.point_b = None
        self.active = False
        return True, f"A point set: {self._format(self.point_a)}"

    def set_b(self, path, position):
        if not path or self.path != path or self.point_a is None:
            return False, "Set A before setting B"
        if position is None:
            return False, "cannot set A-B loop point"
        position = float(position)
        if position <= self.point_a:
            return False, "B point must be after A"
        self.point_b = position
        self.active = True
        return True, f"A-B loop active: {self._format(self.point_a)} - {self._format(self.point_b)}"

    def clear(self):
        self.path = None
        self.point_a = None
        self.point_b = None
        self.active = False

    def update(self, path, position):
        if path != self.path or self.point_a is None or self.point_b is None or position is None:
            return
        try:
            position = float(position)
            if position >= self.point_b:
                if self.active:
                    self.active = False
                    self.engine.command("seek", "%.3f" % self.point_a, "absolute")
            else:
                self.active = True
        except Exception:
            self.active = False

    @staticmethod
    def _format(value):
        seconds = max(0, int(value))
        return f"{seconds // 60:02d}:{seconds % 60:02d}"
