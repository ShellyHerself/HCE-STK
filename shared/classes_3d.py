#from reclaimer.hek.defs.objs.matrices import Matrix
#import math

class Vec3d(list):

    def __init__(self, initializer=()):
        assert isinstance(initializer, (list, tuple, float, int))
        if isinstance(initializer, (list, tuple)):
            assert len(initializer) == 3
            list.__init__(self, initializer)
        # Takes a single number and makes a Vec3d with the number in each of its slots.
        # Used for math where a Vec3d is combined with a single numbers.
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
    
    @property
    def magnitude(self): return (self[0]**2 + self[1]**2 + self[2]**2)**(0.5)
        
    @property
    def inverse(self): return -self

    def __str__(self):
        assert len(self) == 3, list(self)
        return '[x=%s, y=%s, z=%s]' % (self[0], self[1], self[2])

    def __copy__(self):
        return Vec3d([self[0], self[1], self[2]])
        
    def __deepcopy__(self, memo):
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

    def difference(self, other):
        assert isinstance(other, (list, tuple))
        assert len(other) == 3
        return Vec3d(other - self)

    def distance(self, other):
        return magnitude(difference(self, other))

    def unpack(self):
        return self[0], self[1], self[2]
        
    def to_matrix(self):
        return Matrix((self[0], self[1], self[2]))

        
class Quaternion(list):
    
    def __init__(self, initializer=()):
        assert isinstance(initializer, (list, tuple))
        if isinstance(initializer, (list, tuple)):
            assert len(initializer) == 4
            list.__init__(self, [float(initializer[0]), float(initializer[1]), float(initializer[2]), float(initializer[3])])
            
    @property
    def i(self): return self[0]
    @i.setter
    def i(self, new_val): self[0] = float(new_val)

    @property
    def j(self): return self[1]
    @j.setter
    def j(self, new_val): self[1] = float(new_val)

    @property
    def k(self): return self[2]
    @k.setter
    def k(self, new_val): self[2] = float(new_val)
    
    @property
    def w(self): return self[3]
    @w.setter
    def w(self, new_val): self[3] = float(new_val)
    
    @property
    def inverse(self): return -self
    
    def __str__(self):
        return '[i=%f, j=%f, k=%f, w=%f]' % (self[0], self[1], self[2], self[3])

    def __copy(self):
        return Quaternion(self[0], self[1], self[2], self[3])

    def __eq__(self, other):
        assert len(other) == 4
        return ((self[0] == other[0] and self[1] == other[1] and self[2] == other[2]) and ((self[3] == other[3]) or (self[3] == -other[3])))
        
    def __ne__(self, other):
        return (not self == other)

    def __add__(self, other):
        NotImplementedError

    def __sub__(self, other):
        NotImplementedError

    def __mul__(self, other):
        assert len(other) == 4
        ni =  self[0] * other[3] + self[1] * other[2] - self[2] * other[1] + self[3] * other[0]
        nj = -self[0] * other[2] + self[1] * other[3] + self[2] * other[0] + self[3] * other[1]
        nk =  self[0] * other[1] - self[1] * other[0] + self[2] * other[3] + self[3] * other[2]
        nw = -self[0] * other[0] - self[1] * other[1] - self[2] * other[2] + self[3] * other[3]
        return Quaternion(ni, nj, nk, nw)

    def __truediv__(self, other):
        NotImplementedError
        
    def __neg__(self):
        return Quaternion(-self[0], -self[1], -self[2], self[3])
        
    __rmul__ = __mul__
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
        return Quaternion([0.0, 0.0, 0.0, 1.0])
    
    def normalize(self):
        m = (self[0]**2 + self[1]**2 + self[2]**2 + self[3]**2)**0.5
        return Quaternion(self[0]*m, self[1]*m, self[2]*m, self[3]*m)
    
    def unpack(self):
        return self[0], self[1], self[2], self[3]
    
    def to_matrix(self):
        i,j,k,w = self.unpack()
        return Matrix([
        (2*(0.5 - j*j - k*k),   2*(i*j + k*w),         2*(i*k - j*w)),
        (2*(i*j - k*w),         2*(0.5 - k*k - i*i),   2*(j*k + i*w)),
        (2*(i*k + j*w),         2*(j*k - i*w),         2*(0.5 - i*i - j*j)),
        ])
        

class MatrixRow(list):
    '''Implements the minimal methods required for messing with matrix rows'''
    def __neg__(self):
        return MatrixRow(-x for x in self)
    def __add__(self, other):
        new = MatrixRow(self)
        for i in range(len(other)): new[i] += other[i]
        return new
    def __sub__(self, other):
        new = MatrixRow(self)
        for i in range(len(other)): new[i] -= other[i]
        return new
    def __mul__(self, other):
        if isinstance(other, MatrixRow):
            return sum(self[i]*other[i] for i in range(len(self)))
        new = MatrixRow(self)
        for i in range(len(self)): new[i] *= other
        return new
    def __truediv__(self, other):
        if isinstance(other, MatrixRow):
            return sum(self[i]/other[i] for i in range(len(self)))
        new = MatrixRow(self)
        for i in range(len(self)): new[i] /= other
        return new
    def __iadd__(self, other):
        for i in range(len(other)): self[i] += other[i]
        return self
    def __isub__(self, other):
        for i in range(len(other)): self[i] -= other[i]
        return self
    def __imul__(self, other):
        if isinstance(other, MatrixRow):
            return sum(self[i]*other[i] for i in range(len(self)))
        for i in range(len(self)): self[i] *= other
        return self
    def __itruediv__(self, other):
        if isinstance(other, MatrixRow):
            return sum(self[i]/other[i] for i in range(len(self)))
        for i in range(len(self)): self[i] /= other
        return self

    __radd__ = __add__
    __rsub__ = __sub__
    __rmul__ = __mul__
    __rtruediv__ = __truediv__


class Matrix(list):
    width = 1
    height = 1

    def __init__(self, matrix=None, width=1, height=1):
        if matrix is None:
            self.width = width
            self.height = height
            list.__init__(self, (MatrixRow((0,)*width) for i in range(height)))
            return

        matrix_rows = []
        self.height = max(1, len(matrix))
        self.width = -1
        for row in matrix:
            if not hasattr(row, '__iter__'):
                row = [row]
            self.width = max(self.width, len(row))
            assert self.width and len(row) == self.width
            matrix_rows.append(MatrixRow(row[:]))
        list.__init__(self, matrix_rows)

    def __setitem__(self, index, new_row):
        assert len(new_row) == self.width
        list.__setitem__(self, index, MatrixRow(new_row))

    def __delitem__(self, index):
        self[index][:] = (0,)*self.width

    def __str__(self):
        matrix_str = "Matrix([\n%s])"
        insert_str = ''
        for row in self:
            insert_str += '%s,\n' % (row,)
        return matrix_str % insert_str

    def __neg__(self):
        return Matrix([-row for row in self])

    def __add__(self, other):
        assert isinstance(other, Matrix)
        assert self.width == other.width and self.height == other.height
        new = Matrix(self)
        for i in range(len(other)): new[i] += other[i]
        return new

    def __sub__(self, other):
        assert isinstance(other, Matrix)
        assert self.width == other.width and self.height == other.height
        new = Matrix(self)
        for i in range(len(other)): new[i] -= other[i]
        return new

    def __mul__(self, other):
        assert isinstance(other, (Matrix, int, float))
        if not isinstance(other, Matrix):
            new = Matrix(self)
            for row in new:
                row *= other
            return new

        assert self.width == other.height
        # transpose the matrix so its easier to work with
        new = Matrix(width=other.width, height=self.height)
        other = other.transpose

        # loop over each row in the new matrix
        for i in range(new.height):
            # loop over each column in the new matrix
            for j in range(new.width):
                # set the element equal to the dot product of the matrix rows
                new[i][j] = self[i]*other[j]

        return new

    def __truediv__(self, other):
        assert isinstance(other, (Matrix, int, float))
        if not isinstance(other, Matrix):
            new = Matrix(self)
            for row in new:
                row /= other
            return new
        assert self.width == other.height
        return self * other.inverse

    __repr__ = __str__
    __radd__ = __add__
    __rsub__ = __sub__
    __rmul__ = __mul__
    __rtruediv__ = __truediv__

    def __iadd__(self, other):
        assert isinstance(other, Matrix)
        assert self.width == other.width and self.height == other.height
        for i in range(len(other)): self[i] += other[i]
        return self

    def __isub__(self, other):
        assert isinstance(other, Matrix)
        assert self.width == other.width and self.height == other.height
        for i in range(len(other)): self[i] -= other[i]
        return self

    def __imul__(self, other):
        assert isinstance(other, (Matrix, int, float))
        if not isinstance(other, Matrix):
            for row in self:
                row *= other
            return self

        assert self.width == other.height
        # transpose the matrix so its easier to work with
        new = Matrix(width=other.width, height=self.height)
        other = other.transpose

        # loop over each row in the new matrix
        for i in range(new.height):
            # loop over each column in the new matrix
            for j in range(new.width):
                # set the element equal to the dot product of the matrix rows
                new[i][j] = self[i]*other[j]

        # replace the values in this matrix with those in the new matrix
        self.width = 0
        self.height = new.height
        for i in range(self.height):
            self.width = len(self[i])
            self[i] = new[i]

        return self

    def __itruediv__(self, other):
        assert isinstance(other, (Matrix, int, float))
        if not isinstance(other, Matrix):
            for row in self:
                row /= other
            return self
        self *= other.inverse
        return self

    @property
    def determinant(self):
        assert self.width == self.height, "Non-square matrices do not have determinants."
        if self.width == 2:
            return self[0][0] * self[1][1] - self[0][1] * self[1][0]

        d = 0
        sub_matrix = Matrix(width=self.width - 1, height=self.height - 1)
        for i in range(self.width):
            for j in range(sub_matrix.height):
                for k in range(sub_matrix.width):
                    sub_matrix[j][k] = self[j+1][(i + k + 1) % self.width]
            d += self[0][i] * sub_matrix.determinant
            
        return d

    @property
    def transpose(self):
        transpose = Matrix(width=self.height, height=self.width)
        for r in range(self.height):
            for c in range(self.width):
                transpose[c][r] = self[r][c]
        return transpose

    @property
    def inverse(self, determine_best_inverse=True):
        # cannot invert non-square matrices. check for that
        assert self.width == self.height, "Cannot invert non-square matrix."
        assert self.determinant != 0, "Matrix is non-invertible."
        regular = Matrix(self)
        inverse = Matrix(width=self.width, height=self.height)

        # place the identity matrix into the inverse
        for i in range(inverse.width):
            inverse[i][i] = 1.0

        # IN THE FUTURE I NEED TO REARRANGE THE MATRIX SO THE VALUES
        # ALONG THE DIAGONAL ARE GUARANTEED TO BE NON-ZERO. IF THAT
        # CANT BE ACCOMPLISHED FOR ANY COLUMN, ITS COMPONENT IS ZERO.
        # EDIT: It's the future now

        rearrange_rows = False
        # determine if rows need to be rearranged to properly calculate inverse
        for i in range(self.height):
            largest = max(abs(regular[i][j]) for j in range(self.width))
            if abs(regular[i][i]) < largest:
                rearrange_rows = True
                break

        if rearrange_rows:
            nz_diag_row_indices = list(set() for i in range(self.height))
            valid_row_orders = {}

            # determine which rows have a nonzero value on each diagonal
            for i in range(self.height):
                for j in range(self.width):
                    if regular[i][j]:
                        nz_diag_row_indices[j].add(i)

            self._get_valid_diagonal_row_orders(nz_diag_row_indices,
                                                valid_row_orders, regular,
                                                determine_best_inverse)

            assert valid_row_orders, "No valid way to rearrange rows to enable inversion."

            # rearrange rows so diagonals are all non-zero
            orig_regular = list(regular)
            orig_inverse = list(inverse)
            # get the highest weighted row order
            new_row_order = valid_row_orders[max(valid_row_orders)]
            for i in range(len(new_row_order)):
                regular[i] = orig_regular[new_row_order[i]]
                inverse[i] = orig_inverse[new_row_order[i]]


        for i in range(self.height):
            # divide both matrices by their diagonal values
            div = regular[i][i]
            regular[i] /= div
            inverse[i] /= div

            # make copies of the rows that we can multiply for subtraction
            reg_diff = MatrixRow(regular[i])
            inv_diff = MatrixRow(inverse[i])

            # loop over the rows NOT intersecting the column at the diagonal
            for j in range(self.width):
                if i == j:
                    continue
                # get the value that needs to be subtracted from
                # where this row intersects the current column
                mul = regular[j][i]

                # subtract the difference row from each of the
                # rows above it to set everything in the column
                # above an below the diagonal intersection to 0
                regular[j] -= reg_diff*mul
                inverse[j] -= inv_diff*mul

        return inverse

    def _get_valid_diagonal_row_orders(self, row_indices, row_orders,
                                       matrix, choose_best=True,
                                       row_order=(), curr_row_idx=0):
        row_order = list(row_order)
        row_count = len(row_indices)
        if not row_order:
            row_order = [None] * row_count

        # loop over each row with a non-zero value on this diagonal
        for i in row_indices[curr_row_idx]:
            if row_orders and not choose_best:
                # found a valid row arrangement, don't keep checking
                break
            elif i in row_order:
                continue

            row_order[curr_row_idx] = i

            if curr_row_idx + 1 < row_count:
                # check the rest of the rows
                self._get_valid_diagonal_row_orders(row_indices, row_orders,
                                                    matrix, choose_best,
                                                    row_order, curr_row_idx + 1)
            else:
                weight = 1.0
                for j in range(len(row_order)):
                    weight *= matrix[j][row_order[j]]

                # freeze this row order in place
                row_orders[weight] = tuple(row_order)


    def to_quaternion(self):
        m00, m10, m20 = self[0]
        m01, m11, m21 = self[1]
        m02, m12, m22 = self[2]
        tr = m00 + m11 + m22

        if tr > 0:
            s = (tr+1.0)**0.5 * 2
            i = (m21 - m12) / s
            j = (m02 - m20) / s
            k = (m10 - m01) / s
            w = 0.25 * s
        elif m00 > m11 and m00 > m22:
            s = (1.0 + m00 - m11 - m22)**0.5 * 2
            i = 0.25 * s
            j = (m01 + m10) / s
            k = (m02 + m20) / s
            w = (m21 - m12) / s
        elif m11 > m22:
            s = (1.0 + m11 - m00 - m22)**0.5 * 2
            i = (m01 + m10) / s
            j = 0.25 * s
            k = (m12 + m21) / s
            w = (m02 - m20) / s
        else:
            s = (1.0 + m22 - m00 - m11)**0.5 * 2
            i = (m02 + m20) / s
            j = (m12 + m21) / s
            k = 0.25 * s
            w = (m10 - m01) / s

        return Quaternion((i, j, k, w))
    
    def to_vec3d(self):
        return Vec3d((self[0][0], self[1][0], self[2][0]))
    
    

