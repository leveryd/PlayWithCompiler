# coding:utf-8
import copy


class RETURN(object):
    def __init__(self, value):
        """
        :param value:
        """
        # value可能是以下类型
        # Primitive: int, str
        # Symbol: VariableSymbol  ClassSymbol ClosureFunction ClassField
        #
        # 注意 FunctionSymbol 是不可能返回的，如果返回函数，就一定会是 ClosureFunction 类型

        self.value = value

    def get_value(self):
        """
        在 visitExpression 中
        :return:
        """
        if isinstance(self.value, int) or isinstance(self.value, str):
            return self.value
        elif isinstance(self.value, VariableSymbol) or isinstance(self.value, ClassField)\
                or isinstance(self.value, PrimitiveSymbol):
            return self.value.value
        else:
            return self.value


class ClassFunction(object):
    def __init__(self, name, arguments, body_ctx):
        """
        :param name:
        :param arguments:
        :param body_ctx:
        """
        self.name = name
        self.arguments = arguments
        self.body_ctx = body_ctx


class NodeScopeMap(object):
    node_scope_list = []  # [(nodeCtx1, scope1), (nodeCtx2, scope2)]

    @classmethod
    def get(cls, ctx):
        """
        :param ctx:
        :return:
        """
        for node_scope in cls.node_scope_list:
            if ctx == node_scope[0]:
                return node_scope[1]
        return None

    @classmethod
    def set(cls, ctx, scope):
        """
        :param ctx:
        :param scope:
        :return:
        """
        cls.node_scope_list.append((ctx, scope))


class Scope(object):
    def __init__(self, parent_scope, symbol_list, name=""):
        self.parent_scope = parent_scope
        self.symbol_list = symbol_list
        self.need_symbol_list = []   # 本作用域内调用的符号列表
        self.name = name

    def add_symbol(self, symbol):
        """
        当前域中添加符号
        :return:
        """
        self.symbol_list.append(symbol)

    def add_symbol_list(self, symbol_list):
        """
        :param symbol_list:
        :return:
        """
        for i in symbol_list:
            self.add_symbol(copy.copy(i))

    def get_symbol_by_name(self, name):
        """
        :param name:
        :return:
        """
        for symbol in self.symbol_list:
            if symbol.name == name:
                return symbol
        return None

    def add_needed_symbol(self, symbol):
        """
        :param symbol:
        :return:
        """
        flag = True
        for i in self.need_symbol_list:  # symbol去重
            if symbol.name == i.name:
                flag = False
        if flag:
            self.need_symbol_list.append(symbol)

    def __str__(self):
        return self.name


class BlockScope(Scope):
    index = 0

    def set_name(self, index):
        self.name = "block" + str(index)

    def __str__(self):
        return self.name


class Symbol(object):
    pass


class PrimitiveSymbol(Symbol):
    def __init__(self, value):
        """
        :param value:
        """
        self.value = value

    def get_value(self):
        """
        PrimitiveSymbolInstance

        snoopy(PrimitiveSymbolInstance)
        a = PrimitiveSymbolInstance
        :return:
        """
        return int(self.value)


class VariableSymbol(Symbol):

    def __init__(self, ctx, name, value):
        """
        :param name:
        :param value:
        """
        self.name = name
        self.value = value
        self.ctx = ctx

    def get_value(self):
        """
        PrimitiveSymbolInstance

        snoopy(PrimitiveSymbolInstance)
        a = PrimitiveSymbolInstance
        :return:
        """
        if isinstance(self.value, int) or isinstance(self.value, str):
            return self.value
        if isinstance(self.value, PrimitiveSymbol):
            return self.value.get_value()
        elif isinstance(self.value, ClassSymbol):
            return self.value
        elif isinstance(self.value, FunctionSymbol):  # a=func  函数赋值
            return self.value
        else:
            raise ValueError("exception")


class FunctionSymbol(Symbol):

    def __init__(self, ctx, name, arguments, body_ctx):
        """
        :param ctx:
        :param name:
        :param arguments: [VariableSymbol_1, VariableSymbo_2]
        :param body_ctx:
        """
        self.ctx = ctx
        self.name = name
        self.arguments = arguments
        self.body_ctx = body_ctx

    def compute_self_symbols(self):
        """
        计算自己有的符号
        :return:
        """
        scope = NodeScopeMap.get(self.body_ctx.children[0])
        return scope.symbol_list

    def compute_needed_all_symbols(self):
        """
        计算自己需要的所有符号
        :return:
        """
        scope = NodeScopeMap.get(self.body_ctx.children[0])
        return scope.need_symbol_list

    def compute_needed_symbols(self):
        """
        计算需要传给自己的符号
        这个符号列表在return 闭包函数时返回

        在调用闭包函数时，带上这个符号列表
        :return:
        """
        ret = []
        for i in self.compute_needed_all_symbols():
            no_need = False
            for j in self.compute_self_symbols():
                if i.name == j.name:
                    no_need = True
                    break
            if no_need is False:
                ret.append(i)
        return ret

    def get_value(self):
        """
        :return:
        """
        return self


class ClosureFunction(FunctionSymbol):
    def __init__(self, function):
        """
        :param function: 闭包函数
        """
        FunctionSymbol.__init__(self, function.ctx, function.name, function.arguments, function.body_ctx)
        needed_symbols = function.compute_needed_symbols()
        current_scope = Annotated.get_stack_top()

        self.closure_variables = []
        for needed_symbol in needed_symbols:
            for i in current_scope.symbol_list:
                if i.name == needed_symbol.name:
                    self.closure_variables.append(copy.copy(i))


class ClassSymbol(Symbol):
    def __init__(self, ctx, name, functions, fields, classes):
        """
        :param ctx:
        :param name:
        :param functions:
        :param fields:
        :param classes:
        """
        self.ctx = ctx  # classDeclareCtx
        self.name = name
        self.functions = functions  # [ClassFunction]
        self.fields = fields  # [ClassField]
        self.classes = classes  # 还没有实现

    def instance(self):  # 实例化
        """
        :return:
        """
        pass

    def get_filed_by_name(self, name):
        """
        :param name:
        :return:
        """
        pass

    def put_field(self, field):
        """
        :param field:
        :return:
        """
        # 删除原有
        delete_ids = []
        for i in range(0, len(self.fields)):
            ff = self.fields[i]
            if ff.name == field.name:
                delete_ids.append(i)
        for i in delete_ids:
            del self.fields[i]
        self.fields.append(field)

    def new(self):
        """
        :return:
        """
        ctx = self.ctx  # classDeclareCtx   注意这里没有浅拷贝
        name = copy.copy(self.name)
        functions = copy.copy(self.functions)
        fields = copy.copy(self.fields)
        classes = copy.copy(self.classes)
        return ClassSymbol(ctx, name, functions, fields, classes)

    def get_value(self):
        return self


class ClassField(VariableSymbol):
    def __init__(self, variable_symbol):
        """
        :param variable_symbol:
        """
        VariableSymbol.__init__(self, variable_symbol.ctx, variable_symbol.name, variable_symbol.value)


class Annotated(object):
    scope_list = []    # [scope1, scope2]

    """ 带有注解的树 """
    def __init__(self, ast):
        self.ast = ast

    @classmethod
    def push_scope(cls, scope):
        """
        :param scope:
        :return:
        """
        # 在递归调用函数时，如果没有copy scope，就有可能造成死循环
        # block -> function_call_scope -> function_block_scope -> function_call_scope
        # function_call_scope -> function_block_scope -> function_call_scope 死循环
        tmp_scope = copy.copy(scope)
        if len(cls.scope_list) > 0:
            tmp_scope.parent_scope = cls.scope_list[-1]   # 强行指定scope的栈的关系
        cls.scope_list.append(tmp_scope)

    @classmethod
    def pop_scope(cls):
        """
        :return:
        """
        if len(cls.scope_list) > 0:
            ret = cls.scope_list[-1]
            cls.scope_list = cls.scope_list[:-1]
            return ret
        else:
            return None

    @classmethod
    def get_stack_top(cls):
        """
        :return:
        """
        if len(cls.scope_list) > 0:
            return cls.scope_list[-1]
        return None
