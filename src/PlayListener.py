# coding:utf-8
from dist.PlayScriptListener import PlayScriptListener
from src.TypeAndScope import *


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
