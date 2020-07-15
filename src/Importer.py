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

    def Import_MemoryAccesses(self, access: dict) -> dict:
        ret = {}
        for id, acc in access.items():
            if self.id_resolver.IsALiteral(id):
                continue # Literals are irrelevant.
            if self.id_resolver.IsLocal(id):
                continue # Locals are irrelevant.

            ret[id] = ClosedInterval3D(
                acc.cartesian_extent.i_extent.minus,
                acc.cartesian_extent.i_extent.plus,
                acc.cartesian_extent.j_extent.minus,
                acc.cartesian_extent.j_extent.plus,
                acc.vertical_extent.minus,
                acc.vertical_extent.plus,
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
        assert stage.extents.cartesian_extent.i_extent.minus <= 0
        assert stage.extents.cartesian_extent.i_extent.plus >= 0
        assert stage.extents.cartesian_extent.j_extent.minus <= 0
        assert stage.extents.cartesian_extent.j_extent.plus >= 0
        assert stage.extents.vertical_extent.minus <= 0
        assert stage.extents.vertical_extent.plus >= 0
        
        return Stage(
            [self.Import_DoMethod(dm) for dm in stage.doMethods],
            ClosedInterval3D(
                -stage.extents.cartesian_extent.i_extent.minus, # TODO: Fix the sign mess!
                stage.extents.cartesian_extent.i_extent.plus,
                -stage.extents.cartesian_extent.j_extent.minus,
                stage.extents.cartesian_extent.j_extent.plus,
                -stage.extents.vertical_extent.minus,
                stage.extents.vertical_extent.plus
        ))

    def Import_MultiStage(self, multi_stage) -> MultiStage:
        if multi_stage.loopOrder == ExecutionOrder.Parallel.value:
            for s in multi_stage.stages:
                if len(s.doMethods) > 1:
                    print('This parallel MS has a Stage with {} DoMethods!'.format(len(s.doMethods)))
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
