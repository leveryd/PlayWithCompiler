#!/usr/bin/python2
# coding:utf-8
import copy
from antlr4 import *
from dist.PlayScriptLexer import PlayScriptLexer
from dist.PlayScriptParser import PlayScriptParser
from dist.PlayScriptVisitor import PlayScriptVisitor
from dist.PlayScriptListener import PlayScriptListener


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


class PlayVisitor(PlayScriptVisitor):
    def call_func(self, symbol, ctx):
        """
        :param symbol:
        :param ctx:
        :return: None 、 RETURN对象
        """
        # symbol 找到的函数符号

        # 1. 计算参数值
        if ctx.expressionList() is None:  # 没有参数
            arguments_values = []
        else:
            arguments_values = self.visitExpressionList(ctx.expressionList())

        # 2. 生成新的作用域
        arguments = symbol.arguments
        for i in range(0, len(arguments)):
            argument = arguments[i]
            if isinstance(arguments_values[i], VariableSymbol):
                v = arguments_values[i].value
            else:
                v = arguments_values[i]
            argument.value = v
        current_stack_top_scope = Annotated.get_stack_top()  # 当前的作用域当作函数的父域

        # block -> new_scope1 -> function_block -> new_scope2 -> function_block
        import random
        r_str = str(random.randint(0, 10000))
        new_scope = Scope(current_stack_top_scope, [], "call_func_" + r_str)  # 将参数符号放到函数域
        # new_scope = Scope(current_stack_top_scope, argument, "call_func_" + r_str)  # bug

        new_scope.add_symbol_list(arguments)   # 为了防莫名奇妙的问题

        if isinstance(symbol, ClosureFunction):
            for i in symbol.closure_variables:   # 将闭包函数需要的参数值也传入
                new_scope.add_symbol(i)

        # 执行函数
        Annotated.push_scope(new_scope)
        ret = self.visitFunctionBody(symbol.body_ctx)
        Annotated.pop_scope()
        return ret

    def visitIntegerLiteral(self, ctx):
        return int(ctx.getText())

    def visitProg(self, ctx):
        return self.visitBlockStatements(ctx.blockStatements())

    def visitBlockStatements(self, ctx):
        ret = None
        for i in ctx.blockStatement():
            ret = self.visitBlockStatement(i)

            if isinstance(ret, RETURN):
                return ret    # 必须要将RETURN对象传出去，递归调用时才能停止
        return ret

    def visitBlockStatement(self, ctx):
        if ctx.variableDeclarators() is not None:
            return self.visitVariableDeclarators(ctx.variableDeclarators())
        elif ctx.functionDeclaration() is not None:
            return self.visitFunctionDeclaration(ctx.functionDeclaration())
        elif ctx.classDeclaration() is not None:
            return self.visitClassDeclaration(ctx.classDeclaration())
        else:
            return self.visitStatement(ctx.statement())

    def visitClassDeclaration(self, ctx):
        """
        :param ctx:
        :return:
        """
        pass

    def visitFunctionDeclaration(self, ctx):
        """
        :param ctx:
        :return:
        """
        pass   # 函数声明时，不调用visitBlock

    def visitVariableDeclarators(self, ctx):
        # var_type = self.visitTypeType(ctx.typeType())   # 暂时所有变量全部当作数字类型处理
        for i in ctx.variableDeclarator():
            self.visitVariableDeclarator(i)

    def visitVariableDeclarator(self, ctx):
        """
        :param ctx:
        :return:
        """

        if ctx.variableInitializer() is not None:
            v = self.visitExpression(ctx.variableInitializer().expression())
        else:
            v = PrimitiveSymbol(0)

        current_scope = NodeScopeMap.get(ctx)

        # 变量带有作用域
        variable_name = ctx.variableDeclaratorId().getText()
        current_symbol = current_scope.get_symbol_by_name(variable_name)
        current_symbol.value = v.get_value()

    def visitStatement(self, ctx):
        """
        :param ctx:
        :return:
        """
        if ctx.block() is not None:
            return self.visitBlock(ctx.block())
        if ctx.RETURN() is not None:
            if ctx.expression() is None:
                return RETURN(None)
            else:
                ret_value = self.visitExpression(ctx.expression())

                if isinstance(ret_value, FunctionSymbol):  # 闭包函数的处理
                    return RETURN(ClosureFunction(ret_value))
                # RETURN.value 可能的类型
                # int, str
                # Symbol: VariableSymbol FunctionSymbol ClassSymbol ClosureFunction

                return RETURN(ret_value)
        elif ctx.IF() is not None:
            e = self.visitParExpression(ctx.parExpression())
            if e.get_value() >= 0:
                return self.visitStatement(ctx.statement()[0])
        else:
            # print(ctx.statementExpression.getText())
            return self.visitExpression(ctx.statementExpression)

    def visitParExpression(self, ctx):
        """
        :param ctx:
        :return:
        """
        return self.visitExpression(ctx.expression())

    def visitBlock(self, ctx):
        """
        1. 进入块后要实现当前的作用域栈
        :param ctx:
        :return:
        """
        s = NodeScopeMap.get(ctx)
        Annotated.push_scope(s)

        ret = self.visitBlockStatements(ctx.blockStatements())

        Annotated.pop_scope()
        return ret

    def visitExpression(self, ctx):
        """
        :param ctx:
        :return: PrimitiveSymbol ClassField  RETURN RETURN.get_value None
        """
        if ctx.primary() is not None:
            return self.visitPrimary(ctx.primary())
        elif ctx.bop is not None and ctx.bop.text in ["+", "-", "*", "/"]:
            ll = self.visit(ctx.expression(0))   # 暂时全部当作数字处理

            rr = self.visit(ctx.expression(1))  # 暂时全部当作数字处理

            return PrimitiveSymbol(eval("%d%s%d" % (ll.get_value(), ctx.bop.text, rr.get_value())))
        elif ctx.bop is not None and ctx.bop.text == ".":
            variable = self.visitExpression(ctx.expression()[0])

            if not isinstance(variable.value, ClassSymbol):
                raise ValueError("not class instance")

            class_instance = variable.value   # ClassSymbol

            if ctx.IDENTIFIER() is not None:   # 查找属性
                for field in class_instance.fields:
                    if field.name == ctx.IDENTIFIER().getText():
                        return field  # 返回类的属性
            elif ctx.functionCall() is not None:   # 查找函数
                # if functions.name == ctx.IDENTIFIER().getText():

                # 将类的scope压入栈顶，并且field传入实例的值而不是类的值
                class_declaration_ctx = class_instance.ctx
                class_scope = NodeScopeMap.get(class_declaration_ctx)  # 类的scope
                class_instance_scope = Scope(class_scope.parent_scope, [], "class_instance_scope")
                for field in class_instance.fields:  # 实例的field
                    variable_symbol = VariableSymbol(None, field.name, field.value)
                    class_instance_scope.add_symbol(variable_symbol)

                for function in class_instance.functions:
                    function_symbol = FunctionSymbol(None, function.name, function.arguments, function.body_ctx)
                    class_instance_scope.add_symbol(function_symbol)

                Annotated.push_scope(class_instance_scope)

                ret = self.visitFunctionCall(ctx.functionCall())  # 调用类的方法,ret是RETURN实例

                # 调用方法后，实例域的值可能会改变。实例域的值更新实例
                for field in class_instance.fields:  # 实例的field
                    for symbol in class_instance_scope.symbol_list:
                        if isinstance(symbol, VariableSymbol) and symbol.name == field.name:
                            field.value = symbol.value

                Annotated.pop_scope()
                if ret is None:
                    return None
                else:
                    return ret.get_value()

            else:
                raise ValueError("bad IDENTIFIER")

        elif ctx.bop is not None and ctx.bop.text == "=":
            symbol = self.visit(ctx.expression(0))
            ret = self.visit(ctx.expression(1))

            if isinstance(ret, RETURN):  # 函数的return
                symbol.value = ret.get_value()
            else:  # 全部当作Symbol处理
                symbol.value = ret.get_value()

        elif ctx.functionCall() is not None:
            return self.visitFunctionCall(ctx.functionCall())
        else:
            raise ValueError("bad expression")

    def visitPrimary(self, ctx):
        """
        奇怪的点：antlr没有生成visitPrimary
        :param ctx:
        :return:
        """
        if ctx.literal() is not None:
            primitive_symbol = PrimitiveSymbol(ctx.getText())
            return primitive_symbol
        else:  # 暂时全部当作变量
            # 一直向父节点的scope寻找到变量，直到没有父节点
            current_scope = Annotated.get_stack_top()
            while True:

                if current_scope is None:
                    return None   # 没有找到变量
                else:
                    symbol = current_scope.get_symbol_by_name(ctx.getText())
                    if symbol is None:
                        current_scope = current_scope.parent_scope
                    else:
                        return symbol

                # for i in range(0, len(NodeScopeMap.node_scope_list)):
                #     scope = NodeScopeMap.node_scope_list[i][1]
                #     if scope is None:
                #         continue
                #
                #     s = scope.get_symbol_by_name(ctx.getText())
                #     if s is not None:
                #         return s

    def visitFunctionCall(self, ctx):
        """
        存在一个疑问：课程代码直接 调用visitFunctionDeclaration。那么在函数声明时，为啥不会调用函数中的代码?
        :param ctx:
        :return:

        返回值
            调用snoopy_print  None
            没有找到函数  None
            函数body  RETURN
        """
        if ctx.IDENTIFIER() is not None:
            if ctx.IDENTIFIER().getText() == "snoopy_print":   # 内置的函数
                ret = self.visitExpressionList(ctx.expressionList())

                if len(ret) == 1:
                    print(ret[0].get_value())
                else:
                    print(tuple(ret))
            else:
                # 一直向父节点的scope寻找到函数，直到没有父节点
                current_scope = Annotated.get_stack_top()

                while True:
                    # print(current_scope)

                    if current_scope is None:
                        return None
                    else:
                        symbol = current_scope.get_symbol_by_name(ctx.IDENTIFIER().getText())
                        if symbol is None:
                            current_scope = current_scope.parent_scope
                        elif isinstance(symbol, FunctionSymbol):
                            return self.call_func(symbol, ctx)
                        elif isinstance(symbol, ClassSymbol):
                            # symbol 找到的类的符号

                            # 1. 调用类的构造函数
                            # 创建新的scope

                            # 构造对象实例
                            class_instance = symbol.new()
                            # 初始化类的变量
                            class_declare_ctx = class_instance.ctx

                            class_scope = NodeScopeMap.get(class_declare_ctx)

                            instance_scope = copy.copy(class_scope)
                            # 访问类body中的statement
                            Annotated.push_scope(instance_scope)
                            self.visitClassBody(class_declare_ctx.classBody())
                            Annotated.pop_scope()

                            for symbol in instance_scope.symbol_list:
                                if isinstance(symbol, VariableSymbol):
                                    field = ClassField(symbol)
                                    class_instance.put_field(field)

                                elif isinstance(symbol, FunctionSymbol):
                                    class_function = ClassFunction(symbol.name, symbol.arguments, symbol.body_ctx)
                                    class_instance.functions.append(class_function)

                            return class_instance
                        # x = y()  y是变量，是闭包函数的返回值
                        elif isinstance(symbol, VariableSymbol) and isinstance(symbol.value, ClosureFunction):
                            return self.call_func(symbol.value, ctx)
                        # x= func  函数赋值，这里的x是一个变量类型，值是一个function
                        elif isinstance(symbol, VariableSymbol) and isinstance(symbol.value, FunctionSymbol):
                            return self.call_func(symbol.value, ctx)
                        else:
                            raise ValueError("bad symbol")

    def visitClassBody(self, ctx):
        """
        :param ctx:
        :return:
        """
        for i in ctx.classBodyDeclaration():
            self.visitClassBodyDeclaration(i)

    def visitClassBodyDeclaration(self, ctx):
        """
        :param ctx:
        :return:
        """
        return self.visitMemberDeclaration(ctx.memberDeclaration())

    def visitMemberDeclaration(self, ctx):
        """
        :param ctx:
        :return:
        """
        if ctx.fieldDeclaration() is not None:
            self.visitFieldDeclaration(ctx.fieldDeclaration())

    def visitFieldDeclaration(self, ctx):
        """
        :param ctx:
        :return:
        """
        self.visitVariableDeclarators(ctx.variableDeclarators())

    def visitFunctionBody(self, ctx):
        """
        :param ctx:
        :return:
        """
        return self.visitBlock(ctx.block())

    def visitExpressionList(self, ctx):
        """
        :param ctx:
        :return:
        """
        ret = []
        for i in ctx.expression():
            ret.append(self.visitExpression(i))
        return ret

    def visitTypeType(self, ctx):
        """
        :param ctx:
        :return:
        """
        return self.visitClassOrInterfaceType(ctx.classOrInterfaceType())  # 暂只支持类

    def visitClassOrInterfaceType(self, ctx):
        """
        :param ctx:
        :return:
        """
        current_scope = Annotated.get_stack_top()
        class_name = ctx.IDENTIFIER()[0].getText()
        while True:
            symbol = current_scope.get_symbol_by_name(class_name)
            if symbol is not None:
                return symbol
            else:
                current_scope = current_scope.parent_scope


class PlayListener(PlayScriptListener):
    def __init__(self, ast_tree):
        self.ast = ast_tree

    def enterBlock(self, ctx):
        """
        :param ctx:
        :return:
        """
        # 获取 scope栈顶，作为父scope
        parent_scope = Annotated.get_stack_top()

        # 获取当前scope符号，这里没有
        s = BlockScope(parent_scope, [])
        s.set_name(BlockScope.index)

        BlockScope.index += 1

        # 塞入 scope 列表
        Annotated.push_scope(s)

    def exitBlock(self, ctx):
        """
        :param ctx:
        :return:
        """
        # 将当前节点和域信息存储起来，后面ast解析执行时可以用
        NodeScopeMap.set(ctx, Annotated.pop_scope())

    def enterVariableDeclarator(self, ctx):
        """
        :param ctx:
        :return:
        """
        # 获取 scope栈顶，作为当前的scope
        current_scope = Annotated.get_stack_top()

        # 添加符号到当前scope
        variable_symbol = VariableSymbol(ctx, ctx.variableDeclaratorId().IDENTIFIER().getText(), 0)  # 暂时初始化值0
        current_scope.add_symbol(variable_symbol)

        # 将当前节点和域信息存储起来，后面ast解析执行时可以用
        NodeScopeMap.set(ctx, current_scope)

    def enterFunctionDeclaration(self, ctx):
        """
        函数声明时，将函数加入当前scope的symbol列表
        :param ctx:
        :return:
        """
        # 获取scope栈顶，作为当前的scope
        current_scope = Annotated.get_stack_top()

        # 添加符号到当前scope
        argument_symbol_list = []
        arguments = ctx.formalParameters().formalParameterList()

        if arguments is None:  # 没有参数
            arguments = []
        else:
            arguments = arguments.formalParameter()

        for argument in arguments:
            name = argument.variableDeclaratorId().IDENTIFIER().getText()
            variable_symbol = VariableSymbol(None, name, 0)
            argument_symbol_list.append(variable_symbol)
        function_symbol = FunctionSymbol(ctx, ctx.IDENTIFIER().getText(), argument_symbol_list, ctx.functionBody())
        current_scope.add_symbol(function_symbol)

    def enterClassDeclaration(self, ctx):
        """
        :param ctx:
        :return:
        """
        # 将类符号存入当前栈中
        current_scope = Annotated.get_stack_top()
        name = ctx.IDENTIFIER().getText()
        s = ClassSymbol(ctx, name, [], [], None)
        current_scope.add_symbol(s)

        # 解析类变量、函数前，创建一个新栈
        new_scope = Scope(current_scope, [])
        Annotated.push_scope(new_scope)

        NodeScopeMap.set(ctx, new_scope)

    def exitClassDeclaration(self, ctx):
        """
        :param ctx:
        :return:
        """
        Annotated.pop_scope()

    def enterPrimary(self, ctx):
        """
        :param ctx:
        :return:
        """
        current_scope = Annotated.get_stack_top()
        if ctx.IDENTIFIER() is not None:
            variable_symbol = VariableSymbol(ctx,  ctx.IDENTIFIER().getText(), "")
            current_scope.add_needed_symbol(variable_symbol)


def main(line):
    input_stream = InputStream(line)

    # lexing
    lexer = PlayScriptLexer(input_stream)
    stream = CommonTokenStream(lexer)

    # parsing
    parser = PlayScriptParser(stream)
    tree = parser.prog()

    # semantic analysis
    printer = PlayListener(tree)
    walker = ParseTreeWalker()
    walker.walk(printer, tree)

    # 闭包分析
    # for k, v in NodeScopeMap.node_scope_list:
    #     for symbol in v.symbol_list:
    #         if isinstance(symbol, FunctionSymbol):
    #             tmp = symbol.compute_needed_symbols()
    #             print(tmp)

    # use customized visitor to traverse AST
    visitor = PlayVisitor()
    return visitor.visit(tree)


if __name__ == '__main__':
    # main("{int a=2*3+1;a=a+3*2;int b=1+2;snoopy_print(a, b);} {int a=2;}")
    # main("{int a=2;{int b=2;{int c=2;}}snoopy_print(b);} {}")
    # main("{int a=2;{int a=3;snoopy_print(a);}snoopy_print(a);}")
    # main("{int a=2;{a=3;int b=4;snoopy_print(a);}snoopy_print(a);snoopy_print(b);}")
    # main("snoopy_print(2+3);")
    # main("{int x(int a){snoopy_print(a);}x(3);}")

    with open("tests/if.play", "r") as f:
        script = f.read()
    main(script)

    # x = NodeScopeMap.node_scope_list
    # print(x)
