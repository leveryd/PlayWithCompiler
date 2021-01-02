# coding:utf-8
"""
类型检查：
1. 检查赋值是否正确
2. 变量初始化；
3. 表达式里的一些运算，比如加减乘除，是否类型匹配；
4. 返回值的类型；   [这个还没有做]
"""

from dist.PlayScriptListener import PlayScriptListener
from dist.PlayScriptParser import PlayScriptParser
from src.DataStructures import *


class TypeChecker(PlayScriptListener):
    def __init__(self, ast_tree):
        self.ast = ast_tree
        self.compile_error_list = []

    def exitExpression(self, ctx):
        """
        :param ctx:
        :return:
        """

        if ctx.bop is not None and ctx.bop.text == "+":
            pass
        elif ctx.bop is not None and ctx.bop.text == "=":
            ll = NodeAndType.get_type_of_node(ctx.expression(0))

            # 检查左边expression是否是变量
            if not isinstance(ll, VariableSymbol):
                err_msg = "assign left must be a variable,can't be %s = %s" % (ctx.expression(0).getText(),
                                                                               ctx.expression(1).getText())
                err_line = ctx.expression(0).start.line
                self.compile_error_list.append(CompileError(err_msg, err_line))
                return

            # 检查左边变量类型和右边表达式类型是否相等
            rr = NodeAndType.get_type_of_node(ctx.expression(1))
            rr.update_self()
            if isinstance(rr, VariableSymbol):
                flag = type(rr.type) == type(ll.type)
            else:
                flag = type(rr) == type(ll.type)
            if flag is False:
                err_msg = "left's type is not equal right's type,%s = %s" % (ctx.expression(0).getText(),
                                                                             ctx.expression(1).getText())
                err_line = ctx.expression(0).start.line
                self.compile_error_list.append(CompileError(err_msg, err_line))

    def exitFunctionCall(self, ctx):
        """
        :param ctx:
        :return:
        """
        # symbol = NodeAndSymbol.get_symbol_of_node(ctx.)
        # 内置函数没有symbol,暂时先给snoopy_print加白
        if ctx.IDENTIFIER().getText() in ["snoopy_print"]:
            pass
        else:
            symbol = NodeScopeMap.get_symbol(ctx, ctx.IDENTIFIER().getText())
            if isinstance(ctx.parentCtx, PlayScriptParser.ExpressionContext):  # 类调用
                return   # TODO:更详细地检查类方法

            if isinstance(symbol, ClassSymbol):   # 类初始化
                pass
            elif isinstance(symbol, FunctionSymbol):
                pass
            elif isinstance(symbol, VariableSymbol) and isinstance(symbol.type, FunctionSymbol):  # 检查是否闭包函数
                pass
            else:
                err_msg = "'%s' '%s' is not function" % (ctx.getText(), ctx.IDENTIFIER().getText())
                err_line = ctx.start.line
                self.compile_error_list.append(CompileError(err_msg, err_line))

    def exitVariableDeclarator(self, ctx):
        """
        :param ctx:
        :return:
        """
        if ctx.variableInitializer() is not None:
            variable_name = ctx.variableDeclaratorId().IDENTIFIER().getText()
            ll = NodeScopeMap.get_symbol(ctx, variable_name)

            rr = NodeAndType.get_type_of_node(ctx.variableInitializer().expression())  # TODO:支持数组

            if isinstance(rr, type(ll.type)) is False:
                err_msg = "declare variable type does not match right,%s = %s" % (variable_name,
                                                                             ctx.variableInitializer().getText())
                err_line = ctx.start.line
                self.compile_error_list.append(CompileError(err_msg, err_line))
