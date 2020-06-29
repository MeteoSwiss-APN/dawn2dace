import ast
import astunparse
from Intermediates import *
from IdResolver import IdResolver
from Unparser import *

class Importer:
    def __init__(self, id_resolver:IdResolver):
        self.id_resolver = id_resolver

    @staticmethod
    def Import_Interval(interval) -> HalfOpenInterval:
        """ Converts a Dawn interval into a Dawn2Dace interval. """

        if interval.WhichOneof("LowerLevel") == "special_lower_level":
            if interval.special_lower_level == 0:
                begin = 0
            else:
                begin = Symbol('K') - 1
        elif interval.WhichOneof("LowerLevel") == "lower_level":
            begin = interval.lower_level

        begin += interval.lower_offset

        if interval.WhichOneof("UpperLevel") == "special_upper_level":
            if interval.special_upper_level == 0:
                end = 0
            else:
                end = Symbol('K') - 1
        elif interval.WhichOneof("UpperLevel") == "upper_level":
            end = interval.upper_level

        end += interval.upper_offset

        return HalfOpenInterval(begin, end + 1)

    def Import_MemoryAccesses(self, access: dict) -> list:
        ret = {}
        for id, acc in access.items():
            if self.id_resolver.IsALiteral(id):
                continue # Literals don't need processing.

            i_extent = acc.cartesian_extent.i_extent
            j_extent = acc.cartesian_extent.j_extent
            k_extent = acc.vertical_extent

            i = MemoryAccess1D(i_extent.minus, i_extent.plus)
            j = MemoryAccess1D(j_extent.minus, j_extent.plus)
            k = MemoryAccess1D(k_extent.minus, k_extent.plus)

            ret[id] = MemoryAccess3D(i, j, k)
        return ret

    def Import_Statement(self, stmt) -> Statement:
        down_casted_statement = DownCastStatement(stmt)
        return Statement(
            code = stmt,
            line = down_casted_statement.loc.Line,
            reads = self.Import_MemoryAccesses(down_casted_statement.data.accesses.readAccess),
            writes = self.Import_MemoryAccesses(down_casted_statement.data.accesses.writeAccess),
        )

    def Import_DoMethod(self, do_method) -> DoMethod:
        return DoMethod(
            k_interval = self.Import_Interval(do_method.interval),
            statements = [self.Import_Statement(stmt) for stmt in do_method.ast.block_stmt.statements]
        )

    def Import_Stage(self, stage) -> Stage:
        return Stage(
            [self.Import_DoMethod(dm) for dm in stage.doMethods],
            stage.extents.cartesian_extent.i_extent.minus,
            stage.extents.cartesian_extent.i_extent.plus,
            stage.extents.cartesian_extent.j_extent.minus,
            stage.extents.cartesian_extent.j_extent.plus,
            stage.extents.vertical_extent.minus,
            stage.extents.vertical_extent.plus
        )

    def Import_MultiStage(self, multi_stage) -> MultiStage:
        return MultiStage(
            execution_order = multi_stage.loopOrder,
            stages = [self.Import_Stage(s) for s in multi_stage.stages]
        )

    def Import_Stencil(self, stencil) -> Stencil:
        return Stencil(
            [self.Import_MultiStage(s) for s in stencil.multiStages]
        )

    def Import_Stencils(self, stencils: list) -> list:
        return [self.Import_Stencil(s) for s in stencils]
