from __future__ import annotations
import typing, ast
import sympy, sympy.logic.boolalg as boolalg, sympy.core, sympy.core.relational, sympy.core.numbers, sympy.core.add



print_info = True
"""print debug info to the terminal (in ResolvedIf.eliminate_symbol_from_max_min and Increment.eliminate_symbol_from_max_min)"""
simplify_increment_expression = False
"""simplify the increment expression passed to Increment.__init__"""
simplify_condition = False
"""simplify the condition passed to If.__init__ and ResolvedIf.from_condition"""
simplify_dnf = True
"""force sympy.to_dnf to simplify its result (in If.resolve)"""
merge_sibling_increment_statements = True
"""merge two increment statements if they have the same symbol (in StatementBlock.resolve)"""
conjoin_sibling_if_statements = True
"""merge two sibling if clauses if they have the same condition (in StatementBlock.resolve)"""
evaluate_common_subexpressions = True
"""identify common subexpressions, collect them and evaluate them at once (in ResolvedBlock.cse)"""


Inequality = sympy.GreaterThan | sympy.LessThan | sympy.StrictGreaterThan | sympy.StrictLessThan
In_Equality = Inequality | sympy.Equality
Statement = typing.Union["Increment", "If", "For"]


class SympyMaxMinSplitter:
    def __init__(self, symbols : tuple[sympy.Symbol]):
        self._symbols = symbols
        self._replace_arguments : tuple[typing.Any, bool, list[typing.Any]]
        """target_arg, has_symbol, other_args"""
        return

    def _get_args(self, expression : typing.Any) -> typing.Optional[tuple[typing.Any, list[typing.Any], list[typing.Any]]]:
        """returns func, symbol_args, other_args"""
        func = expression.func
        args = list(expression.args)

        other_args : list[typing.Any] = list()
        symbol_args = [arg for arg in args if arg.has(*self._symbols) or other_args.append(arg)]

        if len(symbol_args) == 0:
            return None    # skip this instance of max/min because no symbol

        return func, symbol_args, other_args

    def _replace(self, expression : typing.Any) -> typing.Any:
        target_arg, has_symbol, other_args = self._replace_arguments

        if has_symbol and target_arg not in expression.args:
            return expression

        new_args = [arg for arg in expression.args if arg not in other_args]

        if len(new_args) == 1:
            return new_args[0]

        return expression.func(*new_args)

    def split(self, expression : typing.Any, inequalities : list[Inequality] = []) -> list[tuple[list[Inequality], typing.Any]]:
        for subexpr in sympy.postorder_traversal(expression):
            if subexpr.func in (sympy.Max, sympy.Min):
                args = self._get_args(subexpr)
                if args != None:
                    break
        else:
            return [(inequalities, expression)]

        ret_val : list[tuple[list[Inequality], typing.Any]] = []
        func, symbol_args, other_args = args
        for i, target_arg in enumerate(symbol_args):
            left_args = symbol_args[:i]
            right_args = symbol_args[i+1:] + other_args

            self._replace_arguments = target_arg, True, left_args + right_args
            new_expression = expression.replace(lambda expr: expr.func == func, self._replace)

            new_inequalities = inequalities.copy()
            if func == sympy.Max:
                # target >= left -> left <= target
                new_inequalities += [sympy.LessThan(arg, target_arg) for arg in left_args]
                # target > right -> right < target
                new_inequalities += [sympy.StrictLessThan(arg, target_arg) for arg in right_args]
            else:
                # target <= left
                new_inequalities += [sympy.LessThan(target_arg, arg) for arg in left_args]
                # target < right
                new_inequalities += [sympy.StrictLessThan(target_arg, arg) for arg in right_args]

            ret_val += self.split(new_expression, new_inequalities)

        if other_args:
            left_args = symbol_args
            target_arg = func(*other_args)
            right_args = []

            self._replace_arguments = target_arg, False, left_args + right_args
            new_expression = expression.replace(lambda expr: expr.func == func, self._replace)

            new_inequalities = inequalities.copy()
            if func == sympy.Max:
                new_inequalities += [sympy.LessThan(arg, target_arg) for arg in left_args]
            else:
                new_inequalities += [sympy.LessThan(target_arg, arg) for arg in left_args]

            ret_val += self.split(new_expression, new_inequalities)
            
        return ret_val

    pass


def is_in_equality_tuple(val: tuple[sympy.Basic, ...]) -> typing.TypeGuard[tuple[In_Equality, ...]]:
    return all(isinstance(x, In_Equality) for x in val)
def is_in_equality_or_symbol_tuple(val: tuple[sympy.Basic, ...]) -> typing.TypeGuard[tuple[In_Equality | sympy.Symbol, ...]]:
    return all(isinstance(x, In_Equality | sympy.Symbol) for x in val)

def find_closing(s : str, opening : str = "(", closing : str = ")") -> tuple[int, int]:
    """
    find the first instance of the opening sign and the corresponding closing sign
    returns (-1, -1) on failure
    """
    opening_index = s.find(opening)
    if opening_index == -1:
        return -1, -1

    count = 0
    for i in range(opening_index, len(s)):
        char = s[i]
        if char == opening:
            count += 1
        elif char == closing:
            count -= 1
        if count == 0:
            return opening_index, i

    return -1, -1


class Assignment:
    def __init__(self, symbol : sympy.Symbol, expr : typing.Any):
        self.symbol = symbol
        self.expr = expr
        return

    pass

class Increment:
    def __init__(self, symbol : sympy.Symbol, expression : typing.Any):
        self.symbol = symbol
        if simplify_increment_expression:
            expression = expression.simplify()
        self.expression = expression
        self._split_results : dict[sympy.Symbol, list[tuple[list[Inequality], typing.Any]]] = {}
        return

    def resolve(self) -> ResolvedBlock:
        """identity"""
        return ResolvedBlock([self])

    def eliminate_symbol_from_max_min(self, summation_index : sympy.Symbol, additional_condition : ResolvedIf.Union = sympy.true) -> ResolvedBlock:
        try:
            split_result = self._split_results[summation_index]
        except KeyError:
            if print_info:
                print(f"splitting Increment by {summation_index}: {self.expression}")
            split_result = SympyMaxMinSplitter((summation_index, )).split(self.expression)
            self._split_results[summation_index] = split_result

        return_block = ResolvedBlock()
        for ineqs, expression in split_result:
            condition : typing.Any = sympy.And(*ineqs, additional_condition).simplify()
            assert isinstance(condition, ResolvedIf.Union), f"condition is of unexpected type {type(condition)}"

            return_block.extend(ResolvedIf.from_condition(condition, [Increment(self.symbol, expression)], True))

        return return_block

    def summation(self, summation_index : sympy.Symbol, start : typing.Any, end : typing.Any, additional_conditions : list[In_Equality]) -> ResolvedBlock:
        back = sympy.Add(end, -1)
        summation_symbols = (summation_index, start, back)

        summation = sympy.summation(self.expression, summation_symbols)
        condition : typing.Any = sympy.And(sympy.StrictLessThan(start, end), *additional_conditions)
        assert isinstance(condition, ResolvedIf.Union), f"condition is of unexpected type {type(condition)}"

        return ResolvedIf.from_condition(condition, [Increment(self.symbol, summation)])

    pass

class If: 
    """represents an if statement"""
    def __init__(self, condition : typing.Any, block : StatementBlock):
        if simplify_condition:
            condition = condition.simplify()
        assert isinstance(condition, Inequality | boolalg.BooleanFunction | boolalg.BooleanTrue | boolalg.BooleanFalse), f"condition must be a boolean function or inequality but is {type(condition)}"

        self.condition = condition
        self.block = block
        return

    def negate(self, block : StatementBlock) -> If:
        return If(sympy.Not(self.condition), block)

    def resolve(self) -> ResolvedBlock:
        """
        split into disjunctive normal form and conjugate nested if statements into a single one
        """
        resolved_block = self.block.resolve()

        resolved_conditions : list[ResolvedIf.Union] = []

        if not isinstance(self.condition, boolalg.BooleanFunction):
            resolved_conditions.append(self.condition)
        else:
            dnf_condition = sympy.to_dnf(self.condition, simplify_dnf, True)

            if isinstance(dnf_condition, sympy.And):
                resolved_conditions.append(dnf_condition)
            else:
                assert isinstance(dnf_condition, sympy.Or), f"condition is of unexpected type {type(dnf_condition)}"

                negated_conditions = True
                for eq in dnf_condition.args:
                    condition = sympy.And(negated_conditions, eq)
                    assert isinstance(condition, ResolvedIf.Union), f"condition is of unexpected type {type(condition)}"
                    resolved_conditions.append(condition)
                    negated_conditions = sympy.And(negated_conditions, sympy.Not(eq))
                
        return_block = ResolvedBlock()

        for resolved_condition in resolved_conditions:
            increment_list : list[Increment] = []
            for resolved_statement in resolved_block:
                if isinstance(resolved_statement, Increment):
                    increment_list.append(resolved_statement)
                else:
                    return_block.extend(resolved_statement.conjugate(resolved_condition))

            return_block.extend(ResolvedIf.from_condition(resolved_condition, increment_list, False))

        return return_block

    pass

class For:
    def __init__(self, summation_index : sympy.Symbol, inequalities : list[Inequality], block : StatementBlock):
        self.summation_index = summation_index
        self.block = block
        self.inequalities = inequalities
        for inequality in self.inequalities:
            assert inequality.has(self.summation_index), f"inequality must contain the index {self.summation_index} but is {inequality}"

        return
    
    @staticmethod
    def _split_inequalities(summation_index : sympy.Symbol, inequalities : list[In_Equality]) -> tuple[typing.Any, typing.Any, list[In_Equality]]:
        starts : list[typing.Any] = []
        ends : list[typing.Any] = []
        remaining : list[In_Equality] = []

        inequalities = [in_equality for in_equality in inequalities if in_equality.has(summation_index) or remaining.append(in_equality)]

        reduce_inequalities_result : typing.Any = sympy.reduce_inequalities(inequalities, summation_index)
        if isinstance(reduce_inequalities_result, sympy.And):
            assert is_in_equality_tuple(reduce_inequalities_result.args), f"inequalities must be in conjunctive normal form but are {reduce_inequalities_result}"
            reduced_inequalities = list(reduce_inequalities_result.args)
        elif isinstance(reduce_inequalities_result, In_Equality):
            reduced_inequalities = [reduce_inequalities_result]
        else:
            raise Exception(f"inequalities are of unexpected type {type(reduce_inequalities_result)}")
        
        for in_equality in reduced_inequalities:
            if isinstance(in_equality.lhs, sympy.core.numbers.NegativeInfinity):
                continue

            is_lhs = in_equality.lhs == summation_index

            if in_equality.rel_op == "==":
                if is_lhs: # x = rhs
                    starts.append(in_equality.rhs)
                    ends.append(sympy.Add(in_equality.rhs, 1))
                else:   # lhs = x
                    starts.append(in_equality.lhs)
                    ends.append(sympy.Add(in_equality.lhs, 1))

            elif in_equality.rel_op == "<":
                if is_lhs:  # x < rhs 
                    ends.append(in_equality.rhs)
                else:   # lhs < x
                    starts.append(sympy.Add(in_equality.lhs, 1))

            elif in_equality.rel_op == "<=": 
                if is_lhs:  # x <= rhs 
                    ends.append(sympy.Add(in_equality.rhs, 1))
                else:   # lhs <= x
                    starts.append(in_equality.lhs)
                    
            elif in_equality.rel_op == ">":  
                if is_lhs:  # rhs < x
                    starts.append(sympy.Add(in_equality.rhs, 1))
                else:   # x < lhs
                    ends.append(in_equality.lhs)
                    
            elif in_equality.rel_op == ">=":
                if is_lhs:   # rhs <= x
                    starts.append(in_equality.rhs)
                else:   # x <= lhs
                    ends.append(sympy.Add(in_equality.lhs, 1))

            else:
                raise Exception(in_equality.rel_op)

        return sympy.Max(*starts), sympy.Min(*ends), remaining

    def resolve(self) -> ResolvedBlock:
        """
        merge resolved if statements into the enclosing for statement (or extract them)
        resolve for statement
        """
        resolved_block = self.block.resolve().eliminate_symbol_from_max_min(self.summation_index)
        return_block = ResolvedBlock()
        
        ineqs = typing.cast(list[In_Equality], self.inequalities)
        start, end, remaining = self._split_inequalities(self.summation_index, ineqs)
        assert len(remaining) == 0, f"for statement can't have from {self.summation_index} independant inequalities but has {remaining}"

        for resolved_statement in resolved_block:
            if isinstance(resolved_statement, ResolvedIf):
                if isinstance(resolved_statement.condition, sympy.And):
                    assert is_in_equality_tuple(resolved_statement.condition.args), f"condition must be in conjunctive normal form but is {resolved_statement.condition}"
                    new_inequalities = self.inequalities + [*resolved_statement.condition.args]
                elif isinstance(resolved_statement.condition, In_Equality):
                    new_inequalities = self.inequalities + [resolved_statement.condition]
                else:
                    raise Exception(f"condition is of unexpected type {type(resolved_statement.condition)}")
                
                temp_start, temp_end, additional_conditions = self._split_inequalities(self.summation_index, new_inequalities)

                for increment in resolved_statement.block:
                    return_block.extend(increment.summation(self.summation_index, temp_start, temp_end, additional_conditions))

            else:
                return_block.extend(resolved_statement.summation(self.summation_index, start, end, []))

        return return_block

    pass


class ResolvedIf:
    """represents an if statement whose condition contains only conjunctions of inequalities"""
    Union : typing.TypeAlias = sympy.And | In_Equality | sympy.Symbol | boolalg.BooleanTrue | boolalg.BooleanFalse

    @staticmethod
    def from_condition(condition : Union, block : list[Increment], is_simplified : bool = False) -> ResolvedBlock:
        if not block:
            return ResolvedBlock()

        if simplify_condition and is_simplified == False:
            condition = condition.simplify()
            assert isinstance(condition, ResolvedIf.Union), f"condition is of unexpected type {type(condition)}"

        if isinstance(condition, sympy.And):
            return ResolvedBlock([ResolvedIf(condition, block)])

        elif isinstance(condition, In_Equality | sympy.Symbol):
            return ResolvedBlock([ResolvedIf(condition, block)])

        elif isinstance(condition, boolalg.BooleanTrue):
            return ResolvedBlock(block)

        elif isinstance(condition, boolalg.BooleanFalse):
            return ResolvedBlock()

        raise Exception(f"condition is of unexpected type {type(condition)}")

    def __init__(self, condition : sympy.And | In_Equality | sympy.Symbol, block : list[Increment]):
        if isinstance(condition, sympy.And):
            assert is_in_equality_or_symbol_tuple(condition.args), f"condition must be in conjunctive normal form but is {condition}"
        self.condition = condition
        self.block = block

        return

    def conjugate(self, other_condition : Union) -> ResolvedBlock:
        """
        conjugates self and a condition
        """
        conjugated_condition = sympy.And(self.condition, other_condition)
        assert isinstance(conjugated_condition, ResolvedIf.Union), f"conjugated condition is of unexpected type {type(conjugated_condition)}"
        if isinstance(conjugated_condition, sympy.And):
            assert is_in_equality_or_symbol_tuple(conjugated_condition.args), f"condition must be in conjunctive normal form but is {conjugated_condition}"
        return ResolvedIf.from_condition(conjugated_condition, self.block)

    def eliminate_symbol_from_max_min(self, summation_index : sympy.Symbol) -> ResolvedBlock:
        return_block = ResolvedBlock()
        
        if print_info:
            print(f"splitting ResolvedIf by {summation_index}: {self.condition}")
        split_result = SympyMaxMinSplitter((summation_index, )).split(self.condition)
        for new_inequalities, modified_condition in split_result:
            new_condition = sympy.And(*new_inequalities, modified_condition)
            assert isinstance(new_condition, ResolvedIf.Union), f"new condition is of unexpected type {type(new_condition)}"

            for increment in self.block:
                return_block.extend(increment.eliminate_symbol_from_max_min(summation_index, new_condition))
                
        return return_block

    pass


class StatementBlock(list[Statement]):
    def resolve(self) -> ResolvedBlock:
        """
        merge arithmetic statements with the same symbol, conjoin if statements with the same condition
        """
        
        resolved_statements = ResolvedBlock(resolved_statement for statement in self for resolved_statement in statement.resolve())
        increment_list = [resolved_statement for resolved_statement in resolved_statements if isinstance(resolved_statement, Increment)]
        resolved_if_list = [resolved_statement for resolved_statement in resolved_statements if isinstance(resolved_statement, ResolvedIf)]
        
        # merge increments with the same symbol
        def merge_increment(increment_list : list[Increment]) -> list[Increment]:
            increment_dict : dict[sympy.Symbol, list[Increment]] = {}
            for increment in increment_list:
                increment_dict.setdefault(increment.symbol, []).append(increment)

            return [Increment(symbol, sum(increment.expression for increment in increments)) for symbol, increments in increment_dict.items()]

        # conjoin if statements with the same condition
        if conjoin_sibling_if_statements:
            n = len(resolved_if_list)
            for i in range(n - 1, -1, -1):
                check_resolved_if = resolved_if_list[i]
                for resolved_if in resolved_if_list[:i]:
                    try:
                        equals = resolved_if.condition.equals(check_resolved_if.condition)
                    except NotImplementedError:
                        pass
                    else:
                        if equals:
                            resolved_if.block.extend(check_resolved_if.block)
                            resolved_if_list.pop(i)
                            break


        resolved_block = ResolvedBlock()

        if merge_sibling_increment_statements:
            resolved_block.extend(merge_increment(increment_list))
        else:
            resolved_block.extend(increment_list)

        for resolved_if in resolved_if_list:
            if merge_sibling_increment_statements:
                resolved_if.block = merge_increment(resolved_if.block)
            else:
                resolved_if.block = resolved_if.block
            resolved_block.append(resolved_if)

        return resolved_block

    pass

class ResolvedBlock(list[ResolvedIf | Increment]):
    def eliminate_symbol_from_max_min(self, summation_index : sympy.Symbol) -> ResolvedBlock:
        return ResolvedBlock(resolved_statement for temp_resolved_statement in self for resolved_statement in temp_resolved_statement.eliminate_symbol_from_max_min(summation_index))

    def cse(self) -> CSEBlock:
        expressions : list[typing.Any] = []

        result_symbols : set[sympy.Symbol] = set()

        for statement in self:
            if isinstance(statement, ResolvedIf):
                expressions.append(statement.condition)
                for increment in statement.block:
                    expressions.append(increment.expression)
                    result_symbols.add(increment.symbol)
            else:
                expressions.append(statement.expression)
                result_symbols.add(statement.symbol)

        replacements, reduced_expressions = sympy.cse(expressions)
        assert isinstance(reduced_expressions, list)

        return_block = CSEBlock()
        return_block.extend(Assignment(result_symbol, 0) for result_symbol in result_symbols)

        if evaluate_common_subexpressions:
            return_block.extend(Assignment(replacement[0], replacement[1]) for replacement in replacements)

            for statement in self:
                if isinstance(statement, ResolvedIf):
                    resolved_condition = reduced_expressions.pop(0)
                    assert isinstance(resolved_condition, ResolvedIf.Union), f"resolved condition is of unexpected type {type(resolved_condition)}"
                    new_if = ResolvedIf.from_condition(resolved_condition, [Increment(increment.symbol, reduced_expressions.pop(0)) for increment in statement.block])
                    return_block.extend(new_if)
                else:
                    return_block.append(Increment(statement.symbol, reduced_expressions.pop(0)))
        else:
            return_block.extend(self)

        return return_block

    pass

class CSEBlock(list[ResolvedIf | Increment| Assignment]):
    def dump_python(self) -> str:
        return_string = ""

        for statement in self:
            if isinstance(statement, Increment):
                return_string += f"{sympy.pycode(statement.symbol)} += {sympy.pycode(statement.expression)}\n"

            elif isinstance(statement, ResolvedIf):
                return_string += f"if {sympy.pycode(statement.condition)}:\n"
                for increment in statement.block:
                    return_string += f"    {sympy.pycode(increment.symbol)} += {sympy.pycode(increment.expression)}\n"

            elif isinstance(statement, Assignment):
                return_string += f"{sympy.pycode(statement.symbol)} = {sympy.pycode(statement.expr)}\n"
  
            else:
                raise Exception(f"unexpected statement {statement}")

        return return_string

    def dump_cpp(self, integer_type : str = "long long", force_braces : bool = False, beginning_brace_on_same_line : bool = False) -> str:
        return_string = ""

        for statement in self:
            if isinstance(statement, Increment):
                return_string += f"{sympy.cxxcode(statement.symbol)} += {sympy.cxxcode(statement.expression)};\n"

            elif isinstance(statement, ResolvedIf):
                return_string += f"if ({sympy.cxxcode(statement.condition)})"
                if len(statement.block) != 1 or force_braces:
                    if beginning_brace_on_same_line:
                        return_string += " "
                    else:
                        return_string += "\n"
                    return_string += "{"
                return_string += "\n"
                for increment in statement.block:
                    return_string += f"    {sympy.cxxcode(increment.symbol)} += {sympy.cxxcode(increment.expression)};\n"
                if len(statement.block) != 1 or force_braces:
                    return_string += "}\n"

            elif isinstance(statement, Assignment):
                return_string += f"{integer_type} {sympy.cxxcode(statement.expr, statement.symbol)}\n"
  
            else:
                raise Exception(f"unexpected statement {statement}")

        return return_string

    pass


class Python:
    @staticmethod
    def _parse_block(stmts : list[ast.stmt], sympy_local_dict : dict[str, sympy.Symbol] | None, sum_indices : set[sympy.Symbol],
                     results : set[sympy.Symbol], constants : dict[sympy.Symbol, typing.Any]) -> StatementBlock:
        
        sum_indices = sum_indices.copy()
        results = results.copy()
        constants = constants.copy()
        
        return_block = StatementBlock()
        for stmt in stmts:

            if isinstance(stmt, ast.If):
                condition_string = ast.unparse(stmt.test).replace("&&", "&").replace("||", "|")

                condition = sympy.parse_expr(condition_string, sympy_local_dict).subs(constants)
                If_ = If(condition, Python._parse_block(stmt.body, sympy_local_dict, sum_indices, results, constants))
                return_block.append(If_)

                if len(stmt.orelse) != 0:
                    return_block.append(If_.negate(Python._parse_block(stmt.orelse, sympy_local_dict, sum_indices, results, constants)))

            elif isinstance(stmt, ast.For):
                var = stmt.target
                assert isinstance(var, ast.Name), "the target of the for loop must be a variable"
                sum_index = sympy.parse_expr(ast.unparse(var), sympy_local_dict)
                assert sum_index not in sum_indices, f"can't assign to a summation index at line {stmt.lineno}: '{ast.unparse(stmt)}'"
                assert sum_index not in constants, f"can't reassign to this constant at line {stmt.lineno}: '{ast.unparse(stmt)}'"
                assert sum_index not in results, f"can't reassign to this result at line {stmt.lineno}: '{ast.unparse(stmt)}'"
                sum_indices.add(sum_index)

                rng = stmt.iter
                assert isinstance(rng, ast.Call), "the expression must be a function call"
                assert isinstance(rng.func, ast.Name) and rng.func.id == 'range', "the function called must be 'range'"
                assert len(rng.args) == 2, "the call to 'range' must have exactly two arguments"
                lower = sympy.parse_expr(ast.unparse(rng.args[0]), sympy_local_dict).subs(constants)
                upper = sympy.parse_expr(ast.unparse(rng.args[1]), sympy_local_dict).subs(constants)
                
                lt : typing.Any = sympy.LessThan(lower, sum_index)
                slt : typing.Any = sympy.StrictLessThan(sum_index, upper)
                assert isinstance(lt, Inequality) and isinstance(slt, Inequality), f"range must be a range but is {lt} and {slt}"
                
                return_block.append(For(sum_index, [lt, slt], Python._parse_block(stmt.body, sympy_local_dict, sum_indices, results, constants)))

            elif isinstance(stmt, ast.Assign):  # =
                assert len(stmt.targets) == 1, "can only assign to one variable at a time"

                target = stmt.targets[0]
                assert isinstance(target, ast.Name), "the target of the for loop must be a variable"

                symbol = sympy.parse_expr(ast.unparse(target), sympy_local_dict)
                assert symbol not in sum_indices, f"can't assign to a summation index at line {stmt.lineno}: '{ast.unparse(stmt)}'"
                assert symbol not in constants, f"can't reassign to this constant at line {stmt.lineno}: '{ast.unparse(stmt)}'"
                assert symbol not in results, f"can't reassign to this result at line {stmt.lineno}: '{ast.unparse(stmt)}'"

                expression = sympy.parse_expr(ast.unparse(stmt.value), sympy_local_dict).subs(constants)
                constants[symbol] = expression

            elif isinstance(stmt, ast.AugAssign): # +=
                assert isinstance(stmt.op, ast.Add)
                assert isinstance(stmt.target, ast.Name), "the target of the for loop must be a variable"

                result_symbol = sympy.parse_expr(ast.unparse(stmt.target), sympy_local_dict)
                assert result_symbol not in sum_indices, f"can't assign to a summation index at line {stmt.lineno}: '{ast.unparse(stmt)}'"
                assert result_symbol not in constants, f"can't increment this constant at line {stmt.lineno}: '{ast.unparse(stmt)}'"
                results.add(result_symbol)

                expression = sympy.parse_expr(ast.unparse(stmt.value), sympy_local_dict).subs(constants)

                return_block.append(Increment(result_symbol, expression))

            elif isinstance(stmt, ast.Pass):
                pass

            else:
                raise Exception(f"unknown statement at line {stmt.lineno}: '{ast.unparse(stmt)}'")

            pass
        
        return return_block

    @staticmethod
    def parse(string : str, sympy_local_dict : dict[str, sympy.Symbol] | None = None) -> StatementBlock:
        return Python._parse_block(ast.parse(string).body, sympy_local_dict, set(), set(), dict())

    pass

if __name__ == "__main__":
    python_string = """
for x in range(a + 1, b + 1):
    if c < x:
        r += 2
    if c < x:
        r += x + 1
        r2 += 2 + x
        r += 3*x + 7
        if c < y:
            k = y * 7
            r += max(k, x + 1)
            r += k
            for z in range(q + 1, max(500, x + 1)):
            #for z in range(q + 1, x + 1):
                r += 5
    else:
        r2 += x * 10
    r += x * 2
    """
    
    cse = Python.parse(python_string).resolve().cse()
    print(f"\ncse:\n{cse.dump_python()}")
    print(f"\ncse:\n{cse.dump_cpp()}")
