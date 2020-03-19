import ast
import astunparse
from Intermediates import *
from IdResolver import IdResolver
from Unparser import *

class Importer:
    def __init__(self, id_resolver:IdResolver):
        self.id_resolver = id_resolver

    @staticmethod
    def Import_Interval(interval) -> K_Interval:
        """ Converts a Dawn interval into a Dawn2Dace interval. """

        if interval.WhichOneof("LowerLevel") == "special_lower_level":
            if interval.special_lower_level == 0:
                begin = interval.lower_offset
                begin_relative_to_K = False
            else:
                begin = interval.lower_offset - 1
                begin_relative_to_K = True
        elif interval.WhichOneof("LowerLevel") == "lower_level":
            begin = interval.lower_level + interval.lower_offset
            begin_relative_to_K = False

        if interval.WhichOneof("UpperLevel") == "special_upper_level":
            if interval.special_upper_level == 0:
                end = interval.upper_offset + 1 # +1 to adapt from closed interval to half-open interval
                end_relative_to_K = False
            else:
                end = interval.upper_offset
                end_relative_to_K = True
        elif interval.WhichOneof("UpperLevel") == "upper_level":
            end = interval.upper_level + interval.upper_offset + 1 # +1 to adapt from closed interval to half-open interval
            end_relative_to_K = False

        return K_Interval(HalfOpenInterval(begin, end), begin_relative_to_K, end_relative_to_K)

    def Import_MemoryAccesses(self, access: dict) -> list:
        ret = {}
        for id, acc in access.items():
            if self.id_resolver.IsALiteral(id):
                continue # Literals don't need processing.

            i_extent = acc.cartesian_extent.i_extent
            j_extent = acc.cartesian_extent.j_extent
            k_extent = acc.vertical_extent

            i = RelMemAcc1D(i_extent.minus, i_extent.plus)
            j = RelMemAcc1D(j_extent.minus, j_extent.plus)
            k = RelMemAcc1D(k_extent.minus, k_extent.plus)

            ret[id] = RelMemAcc3D(i, j, k)
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
            do_methods = [self.Import_DoMethod(dm) for dm in stage.doMethods]
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
