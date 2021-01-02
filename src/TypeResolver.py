# coding:utf-8
"""
类型解析，也就是用到了typetype的地方   (只计算I属性?)
1. 变量声明
2. 函数声明
3. 类声明
    * 类的属性类型

"""

from dist.PlayScriptListener import PlayScriptListener
from src.DataStructures import *


class TypeResolver(PlayScriptListener):
    def __init__(self, ast_tree):
        self.ast = ast_tree
        self.compile_error_list = []

    def exitVariableDeclarators(self, ctx):
        """
        在scope中找到symbol，设置symbol的类型
        :param ctx:
        :return:
        """
        variable_type = NodeAndType.get_type_of_node(ctx.typeType())

        # 声明变量部分
        for i in ctx.variableDeclarator():
            variable_name = i.variableDeclaratorId().getText()
            variable_symbol = NodeScopeMap.get_symbol(ctx, variable_name)

            if variable_symbol.type is not None:  # 检查变量是否重复声明
                e = CompileError("redclare variable %s" % variable_name, ctx.start.line)
                self.compile_error_list.append(e)

            variable_symbol.set_type(variable_type)

    def exitFunctionDeclaration(self, ctx):
        """
        在scope中找到symbol，设置symbol的类型
        :param ctx:
        :return:
        """
        function_name = ctx.IDENTIFIER().getText()
        function_symbol = NodeScopeMap.get_symbol(ctx, function_name)

        # function_type = FunctionType()

        if ctx.typeTypeOrVoid() is None:
            # function_type.set_return_type(VoidType())
            function_symbol.set_return_type(VoidType())  # 可能有些多余
        else:
            t = NodeAndType.get_type_of_node(ctx.typeTypeOrVoid())
            # function_type.set_return_type(t)
            function_symbol.set_return_type(t)  # 可能有些多余

        # function_symbol.set_type(function_type)

    def exitFormalParameter(self, ctx):
        """
        :param ctx:
        :return:
        """
        # symbol = NodeAndSymbol.get_symbol_of_node(ctx.variableDeclaratorId())

        variable_name = ctx.variableDeclaratorId().IDENTIFIER().getText()
        symbol = NodeScopeMap.get_symbol(ctx, variable_name)

        symbol_type = NodeAndType.get_type_of_node(ctx.typeType())
        symbol.set_type(symbol_type)

    def exitTypeTypeOrVoid(self, ctx):
        """
        :param ctx:
        :return:
        """
        if ctx.VOID() is not None:
            NodeAndType.put_type_of_node(ctx, VoidType())
        else:  # TypeType
            type_type = NodeAndType.get_type_of_node(ctx.typeType())
            NodeAndType.put_type_of_node(ctx, type_type)

    def exitTypeType(self, ctx):
        """
        :param ctx:
        :return:
        """
        if ctx.primitiveType() is not None:
            NodeAndType.put_type_of_node(ctx, PrimitiveType())
        elif ctx.functionType() is not None:
            function_type = NodeAndType.get_type_of_node(ctx.functionType())
            NodeAndType.put_type_of_node(ctx, function_type)
        elif ctx.classOrInterfaceType() is not None:
            # 暂只支持 ClassName A = ClassName()
            # 不支持 ClassName.ClassFunction A;
            class_symbol_type = NodeAndType.get_type_of_node(ctx.classOrInterfaceType())
            NodeAndType.put_type_of_node(ctx, class_symbol_type)
        else:
            raise ValueError("does not support now")

    def exitClassOrInterfaceType(self, ctx):
        """
        :param ctx:
        :return:
        """
        class_symbol = NodeScopeMap.get_symbol(ctx, ctx.IDENTIFIER(0).getText())

        NodeAndType.put_type_of_node(ctx, class_symbol)

    def exitFunctionType(self, ctx):
        """
        1. 设置函数的返回值
        :param ctx:
        :return:
        """
        # function_type = FunctionType()
        return_type = NodeAndType.get_type_of_node(ctx.typeTypeOrVoid())
        # function_type.set_return_type(return_type)

        function_symbol = FunctionSymbol(None, None, None, None)
        function_symbol.set_return_type(return_type)

        NodeAndType.put_type_of_node(ctx, function_symbol)
