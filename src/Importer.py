import ast
import astunparse
from Intermediates import *
from IdResolver import IdResolver
from Unparser import *
from helpers import RelativeNumber, HalfOpenInterval

class Importer:
    def __init__(self, id_resolver:IdResolver):
        self.id_resolver = id_resolver

    @staticmethod
    def Import_Interval(interval) -> HalfOpenInterval:
        """ Converts a Dawn interval into a Dawn2Dace interval. """

        if interval.WhichOneof("LowerLevel") == "special_lower_level":
            if interval.special_lower_level == 0:
                lower = interval.lower_offset
            else:
                lower = RelativeNumber('K', interval.lower_offset - 1)
        elif interval.WhichOneof("LowerLevel") == "lower_level":
            lower = interval.lower_level + interval.lower_offset

        if interval.WhichOneof("UpperLevel") == "special_upper_level":
            if interval.special_upper_level == 0:
                upper = interval.upper_offset
            else:
                upper = RelativeNumber('K', interval.upper_offset - 1)
        elif interval.WhichOneof("UpperLevel") == "upper_level":
            upper = interval.upper_level + interval.upper_offset

        return HalfOpenInterval(lower, upper + 1) # +1 to adapt from closed interval to half-open interval

    def Import_MemoryAccesses(self, access: dict) -> dict:
        ret = {}
        for id, acc in access.items():
            if self.id_resolver.IsALiteral(id):
                continue # Literals don't have a relative memory access.

            i = acc.cartesian_extent.i_extent
            j = acc.cartesian_extent.j_extent
            k = acc.vertical_extent

            ret[id] = RelMemAcc3D(
                i.minus, i.plus,
                j.minus, j.plus,
                k.minus, k.plus
            )
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
