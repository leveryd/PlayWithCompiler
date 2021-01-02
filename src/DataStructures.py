# coding:utf-8
"""
symbol和type混合了，实际上symbol就是type
"""

import copy


class Type(object):
    pass


class BadType(Type):
    """ 不合法的type """
    pass


class VoidType(Type):
    pass


class PrimitiveType(Type):
    pass


class IntType(PrimitiveType):
    pass


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

    @classmethod
    def get_recursive(cls, ctx):
        """
        递归的找到当前的作用域
        :param ctx:
        :return:
        """
        tmp_ctx = ctx
        while True:
            r = cls.get(tmp_ctx)
            if r is None:
                if tmp_ctx.parentCtx is None:
                    return None
                else:
                    tmp_ctx = tmp_ctx.parentCtx
            else:
                return r

    @classmethod
    def get_symbol(cls, ctx, name):
        """
        从ctx节点递归地向上查找，直到找到name名称的符号
        :param ctx:
        :param name:
        :return:
        """
        tmp_ctx = ctx
        while True:
            r = cls.get(tmp_ctx)
            if r is None:
                if tmp_ctx.parentCtx is None:
                    return None
                else:
                    tmp_ctx = tmp_ctx.parentCtx
            else:
                symbol = r.get_symbol_by_name(name)
                if symbol is None:
                    if tmp_ctx.parentCtx is None:
                        return None
                    else:
                        tmp_ctx = tmp_ctx.parentCtx
                else:
                    return symbol


class NodeAndSymbol(object):
    """ 声明的Node对应的Symbol """
    node_symbol_list = []   # node对应的symbol

    @classmethod
    def get_symbol_of_node(cls, ctx):
        """
        :param ctx:
        :return:
        """
        for i in cls.node_symbol_list:
            if i[0] == ctx:
                return i[1]
        return None

    @classmethod
    def put_symbol_of_node(cls, ctx, symbol):
        """
        :param ctx:
        :param symbol:
        :return:
        """
        cls.node_symbol_list.append((ctx, symbol))


class NodeAndType(object):
    """ 推导出来的Node的Type """
    node_type_list = []

    @classmethod
    def get_type_of_node(cls, ctx):
        """
        :param ctx:
        :return:
        """
        for i in cls.node_type_list:
            # print(i[0].getText())
            if i[0] == ctx:
                return i[1]

    @classmethod
    def put_type_of_node(cls, ctx, t):
        """
        :param ctx:
        :param t:
        :return:
        """
        for i in cls.node_type_list:
            # print(i[0].getText())
            if i[0] == ctx:   # 更新操作
                i[1] = t
                return

        cls.node_type_list.append([ctx, t])


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
        for i in range(0, len(self.symbol_list)):
            s = self.symbol_list[i]
            if s.name == symbol.name:
                print("reduplicate symbol,replace it")
                self.symbol_list[i] = symbol
                return

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


class ClassScope(Scope):
    index = 0

    def set_name(self, index):
        self.name = "class" + str(index)


class FunctionScope(Scope):
    index = 0

    def set_name(self, index):
        self.name = "function" + str(index)


class Symbol(object):
    def __init__(self):
        self.type = None
        self.ctx = None
        self.name = None

    def set_type(self, t):
        """
        设置变量值的类型
        :return:
        """
        self.type = t


class PrimitiveSymbol(Symbol):
    def __init__(self, value):
        """
        :param value:
        """
        Symbol.__init__(self)
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
        Symbol.__init__(self)

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
        elif isinstance(self.value, RETURN):
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
        Symbol.__init__(self)

        self.ctx = ctx
        self.name = name
        self.arguments = arguments
        self.body_ctx = body_ctx
        self.return_type = None

    def set_return_type(self, t):
        """
        :param t:
        :return:
        """
        self.return_type = t

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


class ClassFunction(FunctionSymbol):
    def __init__(self, ctx, name, arguments, body_ctx):
        """
        :param ctx:
        :param name:
        :param arguments:
        :param body_ctx:
        """
        FunctionSymbol.__init__(self, ctx, name, arguments, body_ctx)


class ClosureFunction(FunctionSymbol):
    def __init__(self, function):
        """
        :param function: 闭包函数
        """
        FunctionSymbol.__init__(self, function.ctx, function.name, function.arguments, function.body_ctx)
        needed_symbols = function.compute_needed_symbols()  # 计算自己需要的symbol
        current_scope = Annotated.get_stack_top()

        # 闭包函数特殊的地方：在函数中即将返回闭包函数前，将它所需要的参数打包
        # 从闭包函数一直向上级scope，找到它所需要的参数
        self.closure_variables = []

        for needed_symbol in needed_symbols:
            tmp_scope = current_scope

            found_flag = False
            while True:
                for i in tmp_scope.symbol_list:
                    if i.name == needed_symbol.name:
                        self.closure_variables.append(copy.copy(i))
                        found_flag = True
                        break
                if found_flag is True:
                    break
                elif tmp_scope.parent_scope is None:
                    print("can not found symbol")
                    break
                else:
                    tmp_scope = tmp_scope.parent_scope


class ClassSymbol(Symbol):
    def __init__(self, ctx, name, functions, fields, classes):
        """
        :param ctx:
        :param name:
        :param functions:
        :param fields:
        :param classes:
        """
        Symbol.__init__(self)

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
        for i in self.fields:
            if i.name == name:
                return i
        return None

    def get_func_by_name(self, name):
        """
        :param name:
        :return:
        """
        for i in self.functions:
            if i.name == name:
                return i
        return None

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

    def put_function(self, function):
        """
        :param function:
        :return:
        """
        # 删除原有
        delete_ids = []
        for i in range(0, len(self.functions)):
            ff = self.functions[i]
            if ff.name == function.name:
                delete_ids.append(i)
        for i in delete_ids:
            del self.functions[i]
        self.functions.append(function)

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

    def update_self(self):
        """
        因为顺序逻辑问题有时候类型系统出错，所以修改类型信息统一修改NodeAndSymbol中的Symbol。

        1. 尤其是类的类型信息，全部修改NodeAndSymbol中的Symbol。
        2. 变量的类型信息，另看？
        :return:
        """
        scope = NodeScopeMap.get(self.ctx)
        self.fields = []
        self.functions = []
        # 更新
        for symbol in scope.symbol_list:
            if isinstance(symbol, FunctionSymbol):
                self.functions.append(symbol)

            if isinstance(symbol, VariableSymbol):
                self.fields.append(symbol)


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


class CompileError(object):
    def __init__(self, err_msg, err_line):
        self.err_msg = err_msg
        self.err_line = err_line
