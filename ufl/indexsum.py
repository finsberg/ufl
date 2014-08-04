"""This module defines the IndexSum class."""

# Copyright (C) 2008-2014 Martin Sandve Alnes
#
# This file is part of UFL.
#
# UFL is free software: you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# UFL is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with UFL. If not, see <http://www.gnu.org/licenses/>.

from six.moves import xrange as range

from ufl.log import error
from ufl.assertions import ufl_assert
from ufl.expr import Expr
from ufl.operatorbase import Operator
from ufl.indexing import Index, MultiIndex, as_multi_index
from ufl.precedence import parstr
from ufl.common import EmptyDict
from ufl.core.ufl_type import ufl_type

#--- Sum over an index ---

@ufl_type(num_ops=2)
class IndexSum(Operator):
    __slots__ = ("_dimension",
                 "_free_indices", "_index_dimensions")
                 #"ufl_free_indices", "ufl_index_dimensions") # INDEXING

    def __new__(cls, summand, index):
        if not isinstance(summand, Expr):
            error("Expecting Expr instance, not %s." % repr(summand))
        if not isinstance(index, MultiIndex):
            error("Expecting MultiIndex instance, not %s." % repr(index))
        if len(index) != 1:
            error("Expecting a single Index only.")

        from ufl.constantvalue import Zero
        if isinstance(summand, Zero):
            sh = summand.ufl_shape
            j, = index
            fi = tuple(i for i in summand.free_indices() if not i == j)
            idims = dict(summand.index_dimensions())
            del idims[j]
            return Zero(sh, fi, idims)

        return Operator.__new__(cls)

    def __init__(self, summand, index):
        j, = index

        self._free_indices = tuple(i for i in summand.free_indices() if not i == j)
        self._index_dimensions = dict(summand.index_dimensions())
        self._dimension = self._index_dimensions.pop(j)

        if not self._index_dimensions:
            self._index_dimensions = EmptyDict

        Operator.__init__(self, (summand, index))

    def index(self):
        return self.ufl_operands[1][0]

    def dimension(self):
        return self._dimension

    @property
    def ufl_shape(self):
        return self.ufl_operands[0].ufl_shape

    def free_indices(self):
        return self._free_indices

    def index_dimensions(self):
        return self._index_dimensions

    def is_cellwise_constant(self):
        "Return whether this expression is spatially constant over each cell."
        return self.ufl_operands[0].is_cellwise_constant()

    def evaluate(self, x, mapping, component, index_values):
        i, = self.ufl_operands[1]
        tmp = 0
        for k in range(self._dimension):
            index_values.push(i, k)
            tmp += self.ufl_operands[0].evaluate(x, mapping, component, index_values)
            index_values.pop()
        return tmp

    def __str__(self):
        return "sum_{%s} %s " % (str(self.ufl_operands[1]), parstr(self.ufl_operands[0], self))

    def __repr__(self):
        return "IndexSum(%r, %r)" % (self.ufl_operands[0], self.ufl_operands[1])
