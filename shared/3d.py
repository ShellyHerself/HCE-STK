
class Vec3d(list):

    def __init__(self, initializer=()):
        assert isinstance(initializer, (list, tuple, float, int))
        # Turns tuples, lists and 3 vector matrices (Reclaimer) into vec3d.
        if isinstance(initializer, (list, tuple)):
            assert len(initializer) == 3
            list.__init__(self, initializer[:])
            for i in range(3):
                if isinstance(self[i], (list, tuple)):
                    assert len(self[i]) == 1
                    assert isinstance(self[i][0], (float, int))
                    self[i] = float(self[i][0])
                else:
                    assert isinstance(self[i], (float, int))
                    self[i] = float(self[i])
        # Takes a single number and makes a Vec3d with the number in every slots.
        # Used for math where a Vec3d is combined with a single numbers.
        # This technically makes single numbers valid input.
        elif isinstance(initializer, (float, int)):
            list.__init__(self, [float(initializer), float(initializer), float(initializer)])


    @property
    def x(self): return self[0]
    @x.setter
    def x(self, new_val): self[0] = float(new_val)

    @property
    def y(self): return self[1]
    @y.setter
    def y(self, new_val): self[1] = float(new_val)

    @property
    def z(self): return self[2]
    @z.setter
    def z(self, new_val): self[2] = float(new_val)

    def __str__(self):
        return '[x=%s, y=%s, z=%s]' % (self[0], self[1], self[2])

    def __copy(self):
        return Vec3d([self[0], self[1], self[2]])

    def __eq__(self, other):
        other = Vec3d(other)
        return (self[0] == other[0] and self[1] == other[1] and self[2] == other[2])

    def __ne__(self, other):
        other = Vec3d(other)
        return (self[0] != other[0] and self[1] != other[1] and self[2] != other[2])

    def __add__(self, other):
        other = Vec3d(other)
        return Vec3d([self[0] + other[0], self[1] + other[1], self[2] + other[2]])

    def __sub__(self, other):
        other = Vec3d(other)
        return Vec3d([self[0] - other[0], self[1] - other[1], self[2] - other[2]])

    def __mul__(self, other):
        other = Vec3d(other)
        return Vec3d([self[0] * other[0], self[1] * other[1], self[2] * other[2]])

    def __truediv__(self, other):
        other = Vec3d(other)
        return Vec3d([self[0] / other[0], self[1] / other[1], self[2] / other[2]])

    def __neg__(self):
        return Vec3d([-self[0], -self[1], -self[2]])

    __radd__ = __add__
    __rsub__ = __sub__
    __rmul__ = __mul__
    __rtruediv__ = __truediv__

    def append(self, other):
        NotImplementedError

    def extend(self, other):
        NotImplementedError

    def __delitem__(self, other):
        NotImplementedError

    def clear(self):
        return Vec3d([0.0, 0.0, 0.0])

    def almost_equals(self, other):
        other = Vec3d(other)
        return (nearly_equal(self[0], other[0])
        and     nearly_equal(self[1], other[1])
        and     nearly_equal(self[2], other[2]))

    def magnitude(self):
        return (self[0]**2 + self[1]**2 + self[2]**2)**(0.5)

    def difference(self, other):
        assert isinstance(other, (list, tuple))
        assert len(other) == 3
        return Vec3d(other - self)

    def distance(self, other):
        return magnitude(difference(self, other))

    def unpack(self):
        return self[0], self[1], self[2]
