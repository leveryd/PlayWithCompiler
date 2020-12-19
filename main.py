#!/usr/bin/python2
# coding:utf-8
import random
from antlr4 import *
from dist.PlayScriptLexer import PlayScriptLexer
from dist.PlayScriptParser import PlayScriptParser
from dist.PlayScriptVisitor import PlayScriptVisitor
from dist.PlayScriptListener import PlayScriptListener


vars_list = {}

map_node_scope = {}


class TmpCtx(object):
    def __init__(self, ctx):
        self.parentCtx = ctx
        self.index = random.randint(0, 1000)

    def __str__(self):
        return "tmpCtx " + str(self.index)


class NodeScopeMap(object):   # 因为map_node_scope key是ctx对象时有点问题，所以用此类代替
    node_scope_list = []

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
    def __init__(self, parent_scope, symbol_list):
        self.parent_scope = parent_scope
        self.symbol_list = symbol_list
        self.name = ""

    def add_symbol(self, symbol):
        """
        当前域中添加符号
        :return:
        """
        self.symbol_list.append(symbol)

    def get_symbol_by_name(self, name):
        """
        :param name:
        :return:
        """
        for symbol in self.symbol_list:
            if symbol.name == name:
                return symbol
        return None


class Symbol(object):
    pass


class VariableSymbol(Symbol):

    def __init__(self, ctx, name, value):
        """
        :param name:
        :param value:
        """
        self.name = name
        self.value = value
        self.ctx = ctx


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


class BlockScope(Scope):
    index = 0

    def set_name(self, index):
        self.name = "block" + str(index)

    def __str__(self):
        return self.name


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
        cls.scope_list.append(scope)

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
    def visitIntegerLiteral(self, ctx):
        return int(ctx.getText())

    def visitProg(self, ctx):
        return self.visitBlockStatements(ctx.blockStatements())

    def visitBlockStatements(self, ctx):
        ret = None
        for i in ctx.blockStatement():
            ret = self.visitBlockStatement(i)
            if i.statement() is not None:
                if i.statement().RETURN() is not None:
                    return ret
        return ret

    def visitBlockStatement(self, ctx):
        if ctx.variableDeclarators() is not None:
            return self.visitVariableDeclarators(ctx.variableDeclarators())
        elif ctx.functionDeclaration() is not None:
            return self.visitFunctionDeclaration(ctx.functionDeclaration())
        else:
            return self.visitStatement(ctx.statement())

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
            v = 0

        current_scope = NodeScopeMap.get(ctx)

        # 变量带有作用域
        variable_name = ctx.variableDeclaratorId().getText()
        current_symbol = current_scope.get_symbol_by_name(variable_name)
        current_symbol.value = v

    def visitTypeType(self, ctx):
        return ctx.primitiveType().getText()

    def visitStatement(self, ctx):
        if ctx.block() is not None:
            return self.visitBlock(ctx.block())
        if ctx.RETURN() is not None:
            if ctx.expression() is None:
                return None
            else:
                return self.visitExpression(ctx.expression())
        else:
            return self.visitExpression(ctx.statementExpression)

    def visitBlock(self, ctx):
        """
        :param ctx:
        :return:
        """
        # if ctx.parentCtx is not None and ctx.parentCtx.parentCtx:  # 如果
        return self.visitBlockStatements(ctx.blockStatements())

    def visitExpression(self, ctx):
        if ctx.primary() is not None:
            return self.visitPrimary(ctx.primary())
        elif ctx.bop is not None and ctx.bop.text in ["+", "-", "*", "/"]:
            ll = self.visit(ctx.expression(0))   # 暂时全部当作数字处理
            if isinstance(ll, VariableSymbol):
                l_value = int(ll.value)
            else:
                l_value = int(ll)

            rr = self.visit(ctx.expression(1))  # 暂时全部当作数字处理
            if isinstance(rr, VariableSymbol):
                r_value = int(rr.value)
            else:
                r_value = int(rr)

            return eval("%d%s%d" % (l_value, ctx.bop.text, r_value))
        elif ctx.bop is not None and ctx.bop.text == "=":
            # ll = ctx.expression(0).getText()
            # rr = self.visit(ctx.expression(1))
            # vars_list[ll] = rr
            symbol = self.visit(ctx.expression(0))
            symbol.value = int(self.visit(ctx.expression(1)))
            return None
        elif ctx.functionCall() is not None:
            return self.visitFunctionCall(ctx.functionCall())

    def visitPrimary(self, ctx):
        """
        奇怪的点：antlr没有生成visitPrimary
        :param ctx:
        :return:
        """
        if ctx.literal() is not None:
            return ctx.getText()
        else:  # 暂时全部当作变量
            parent_ctx = ctx
            # 一直向父节点的scope寻找到变量，直到没有父节点
            while True:
                current_scope = NodeScopeMap.get(parent_ctx)
                if current_scope is None:
                    parent_ctx = parent_ctx.parentCtx
                    if parent_ctx is None:
                        break
                else:
                    symbol = current_scope.get_symbol_by_name(ctx.getText())
                    if symbol is None:
                        parent_ctx = parent_ctx.parentCtx
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
        """
        if ctx.IDENTIFIER() is not None:
            if ctx.IDENTIFIER().getText() == "snoopy_print":   # 内置的函数
                ret = self.visitExpressionList(ctx.expressionList())

                if len(ret) == 1:
                    if isinstance(ret[0], Symbol):
                        print(ret[0].value)
                    else:
                        print(ret[0])
                else:
                    print(tuple(ret))
            else:
                # 一直向父节点的scope寻找到函数，直到没有父节点
                parent_ctx = ctx

                while True:
                    current_scope = NodeScopeMap.get(parent_ctx)
                    # print(str(type(parent_ctx)))
                    if isinstance(parent_ctx, TmpCtx):
                        print(parent_ctx)

                    if current_scope is None:
                        parent_ctx = parent_ctx.parentCtx
                        if parent_ctx is None:
                            break
                    else:
                        symbol = current_scope.get_symbol_by_name(ctx.IDENTIFIER().getText())
                        if symbol is None:
                            parent_ctx = parent_ctx.parentCtx
                        else:
                            # symbol 找到的函数符号

                            # 1. 计算参数值
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
                            current_scope = Annotated.get_stack_top()  # 当前的作用域当作函数的父域
                            new_scope = Scope(current_scope, arguments)  # 将参数符号放到函数域
                            Annotated.push_scope(new_scope)  # 函数域到栈顶

                            # 递归时的作用域数据结构
                            # 第一次调用函数时
                            # prog -> block -> statement -> expression -> functionCall
                            # functionBody.parentCtx -> tmp_ctx1 -> functionCallCtx

                            # functionBody -> block -> statement -> expression -> functionCall
                            # functionBody.parentCtx -> tmp_ctx1 -> functionCallCtx

                            # functionBody -> block -> statement -> expression -> functionCall
                            # functionBody.parentCtx -> tmp_ctx1 -> functionCallCtx

                            # functionBody -> block -> statement -> expression -> functionCall

                            # Annotated.scope_list = [scope0, tmp_scope1]
                            # node_scope_list = [(main_block0, scope0), (tmp_ctx1, tmp_scope1)]
                            # functionbody.parentCtx = tmp_ctx1
                            # tmp_ctx1.parentCtx = functioncallCtx
                            # functioncallCtx.parentCtx -> mainBlock

                            # 第一次递归时调用函数时
                            # functionBody -> block -> statement -> expression -> functionCall

                            # Annotated.scope_list = [scope0, tmp_scope1, tmp_scope2]
                            # node_scope_list = [(block0, scope0), (tmp_ctx1, tmp_scope1), (tmp_ctx2, tmp_scope2)]
                            # functionbody.parentCtx = tmp_ctx2
                            # tmp_ctx2.parentCtx = functioncallCtx
                            # functioncallCtx -> expression -> statenment ->.. ->  -> functionDeclaration ->

                            # 虚拟的中间ctx,这里实现得有些问题
                            tmp_ctx = TmpCtx(ctx)

                            NodeScopeMap.set(tmp_ctx, new_scope)
                            # NodeScopeMap.set(ctx, current_scope)

                            # 3. 解析函数block

                            # 将调用函数body的父亲节点改成当前节点，以便函数body找变量
                            # 这里实现得也有问题
                            # symbol.body_ctx.parentCtx = tmp_ctx
                            import copy
                            copy_body_ctx = copy.copy(symbol.body_ctx)
                            copy_body_ctx.parentCtx = tmp_ctx    # 为了递归调用,所以使用copy.copy
                            return self.visitFunctionBody(copy_body_ctx)

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

        # 将当前节点和域信息存储起来，后面ast解析执行时可以用。  这里后面应该是用不着的
        NodeScopeMap.set(ctx, current_scope)


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

    with open("tests/test.play", "r") as f:
        script = f.read()
    main(script)

    # x = NodeScopeMap.node_scope_list
    # print(x)
