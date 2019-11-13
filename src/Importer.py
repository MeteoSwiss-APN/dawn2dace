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
        """ Converts a Dawn interval into a Dawn2Dice interval. """

        if interval.WhichOneof("LowerLevel") == "special_lower_level":
            if interval.special_lower_level == 0:
                begin = "0"
                sort_key = 0
            else:
                begin = "K-1"
                sort_key = 10000 - 1
        elif interval.WhichOneof("LowerLevel") == "lower_level":
            begin = str(interval.lower_level)
            sort_key = interval.lower_level

        begin += "+" + str(interval.lower_offset)
        sort_key += interval.lower_offset

        if interval.WhichOneof("UpperLevel") == "special_upper_level":
            if interval.special_upper_level == 0:
                end = "0"
            else:
                # intervals are adapted to be inclusive so K-1 is what we want (starting from 0)
                end = "K-1"
        elif interval.WhichOneof("UpperLevel") == "upper_level":
            end = str(interval.upper_level)

        end += "+" + str(interval.upper_offset)
        end += "+1" # since python interval are open we need to add 1.

        return K_Interval(begin, end, sort_key)

    def Import_MemoryAccesses(self, access: dict) -> list:
        ret = []
        for id, acc in access.items():
            if id < 0: # is a literal variable
                continue # No need to process.
            else:
                i = acc.cartesian_extent.i_extent
                j = acc.cartesian_extent.j_extent
                k = acc.vertical_extent
                i = MemoryAccess1D(i.minus, i.plus)
                j = MemoryAccess1D(j.minus, j.plus)
                k = MemoryAccess1D(k.minus, k.plus)
                ret.append(MemoryAccess3D(id, i, j, k))
        return ret

    def Import_Statement(self, stmt) -> Statement:
        data = DownCastStatement(stmt).data
        code = Unparser(data.accesses.readAccess).unparse_body_stmt(stmt)
        return Statement(
            code = code,
            reads = self.Import_MemoryAccesses(data.accesses.readAccess),
            writes = self.Import_MemoryAccesses(data.accesses.writeAccess),
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
