# coding:utf-8
"""
1. 识别所有的作用域，包括block、function、class
2. 识别所有的符号，包括variable_symbol、类的定义、函数的定义
"""
from dist.PlayScriptListener import PlayScriptListener
from src.DataStructures import *


class ScanScopes(PlayScriptListener):
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
        NodeScopeMap.set(ctx, s)

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

        # 新建scope
        # 获取当前scope符号，这里没有
        function_scope = FunctionScope(current_scope, [])
        function_scope.set_name(FunctionScope.index)

        FunctionScope.index += 1

        for argument in arguments:
            name = argument.variableDeclaratorId().IDENTIFIER().getText()
            variable_symbol = VariableSymbol(argument.variableDeclaratorId(), name, 0)
            argument_symbol_list.append(variable_symbol)
            function_scope.add_symbol(variable_symbol)   # 这里的符号检查会用到，函数调用时不会用到这个符号

        function_symbol = FunctionSymbol(ctx, ctx.IDENTIFIER().getText(), argument_symbol_list, ctx.functionBody())
        current_scope.add_symbol(function_symbol)

        # 在scope栈中压入函数scope
        Annotated.push_scope(function_scope)

    def exitFunctionDeclaration(self, ctx):
        """
        :param ctx:
        :return:
        """
        # 将当前节点和域信息存储起来，后面ast解析执行时可以用
        NodeScopeMap.set(ctx, Annotated.pop_scope())

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
        new_scope = ClassScope(current_scope, [])
        Annotated.push_scope(new_scope)

        # 支持继承：将父类的变量和函数添加到本ClassScope中
        if ctx.typeType() is not None:
            parent_class_name = ctx.typeType().classOrInterfaceType().IDENTIFIER()[0].getText()  # TODO:支持A.B的写法
            parent_class_symbol = NodeScopeMap.get_symbol(ctx, parent_class_name)
            parent_class_scope = NodeScopeMap.get(parent_class_symbol.ctx)
            # TODO:递归地支持父类的父类
            for symbol in parent_class_scope.symbol_list:
                new_scope.add_symbol(symbol)

        NodeScopeMap.set(ctx, new_scope)

    def exitClassDeclaration(self, ctx):
        """
        :param ctx:
        :return:
        """
        # 填充类的属性和函数,同时更新了NodeScopeMap中类的定义
        # class_scope = Annotated.pop_scope()
        # class_symbol = NodeScopeMap.get_symbol(ctx, ctx.IDENTIFIER().getText())
        # for symbol in class_scope.symbol_list:
        #     if isinstance(symbol, VariableSymbol):
        #         class_symbol.put_field(symbol)
        #     elif isinstance(symbol, FunctionSymbol):
        #         class_symbol.put_function(symbol)
        #     else:
        #         raise ValueError("should not be here")
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

    def exitVariableDeclaratorId(self, ctx):
        """
        把所有的变量符号全部存入
        :param ctx:
        :return:
        """
        variable_name = ctx.IDENTIFIER().getText()
        # NodeAndSymbol.put_symbol_of_node(ctx, VariableSymbol(ctx, variable_name, 0))
