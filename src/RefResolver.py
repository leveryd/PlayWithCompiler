# coding:utf-8
"""
类型解析，计算S属性 和 类型推导

类的属性是类的情况
"""

from dist.PlayScriptListener import PlayScriptListener
from dist.PlayScriptParser import PlayScriptParser
from src.DataStructures import *


class RefResolver(PlayScriptListener):
    def __init__(self, ast_tree):
        self.ast = ast_tree
        self.compile_err_list = []

    def exitPrimary(self, ctx):
        """
        :param ctx:
        :return:
        """
        if ctx.literal() is not None:
            t = PrimitiveType()
            NodeAndType.put_type_of_node(ctx, t)
        elif ctx.IDENTIFIER() is not None:
            symbol = NodeScopeMap.get_symbol(ctx, ctx.IDENTIFIER().getText())
            if symbol is None:  # 未找到变量定义
                e = CompileError("no declare for variable '%s'" % ctx.IDENTIFIER().getText(), ctx.start.line)
                self.compile_err_list.append(e)
            else:
                # NodeAndSymbol.put_symbol_of_node(ctx, symbol.type)
                NodeAndType.put_type_of_node(ctx, symbol)
        else:
            raise ValueError("does not support other primary")   # 其他的都暂时不支持

    def exitFunctionCall(self, ctx):
        """
        :param ctx:
        :return:
        """
        function_name = ctx.IDENTIFIER().getText()
        if function_name in ["snoopy_print"]:
            return

        function_symbol = NodeScopeMap.get_symbol(ctx, function_name)

        if isinstance(function_symbol, FunctionSymbol):   # 调用普通函数
            NodeAndType.put_type_of_node(ctx, function_symbol.return_type)
        elif isinstance(function_symbol, VariableSymbol):   # 闭包处理
            variable_value_type = function_symbol.type
            if not isinstance(variable_value_type, FunctionSymbol):
                # e = CompileError("'%s' is not function" % function_symbol.name, ctx.start.line)
                # self.compile_err_list.append(e)
                pass
            else:
                NodeAndType.put_type_of_node(ctx, variable_value_type.return_type)   # 闭包函数变量
        elif isinstance(ctx.parentCtx, PlayScriptParser.ExpressionContext) and \
                ctx.parentCtx.bop is not None and ctx.parentCtx.bop.text == ".":   # 类的方法
            pass
        elif isinstance(function_symbol, ClassSymbol):  # 类初始化
            NodeAndType.put_type_of_node(ctx, function_symbol)
        elif function_symbol is None:
            e = CompileError("no declare for variable '%s'" % function_name, ctx.start.line)
            self.compile_err_list.append(e)
        else:
            raise ValueError("not support function call")

    def exitExpression(self, ctx):
        """
        :param ctx:
        :return:
        """

        def can_operate(symbol):
            """
            symbol是否可以做逻辑操作 + - * /
            :param symbol:
            :return:
            """
            if isinstance(symbol, PrimitiveType):
                return True
            elif isinstance(symbol, VariableSymbol) and isinstance(symbol.type, PrimitiveType):
                return True
            else:
                return False
        # t = NodeAndType.get_type_of_node(ctx)
        # if t is not None:   # 如果已经有这个类型，就不处理
        #     return

        if ctx.primary() is not None:
            t = NodeAndType.get_type_of_node(ctx.primary())
            NodeAndType.put_type_of_node(ctx, t)
        elif ctx.functionCall() is not None and ctx.bop is None:   # 调用函数
            # return返回值当作expr类型
            # 只处理普通方法的调用，不处理类方法的调用

            # 加白内置函数 # 加白内置函数
            function_name = ctx.functionCall().IDENTIFIER().getText()

            if function_name in ["snoopy_print"]:
                return

            # 没有找到symbol时，可能是类的方法
            # 找到symbol时，可能是普通方法、类初始化函数
            symbol = NodeScopeMap.get_symbol(ctx, function_name)
            if symbol is None:
                if isinstance(ctx.parentCtx, PlayScriptParser.ExpressionContext):  # 类方法
                    pass  # TODO:支持
                else:
                    e = CompileError("no declare for variable '%s'" % function_name, ctx.start.line)
                    self.compile_err_list.append(e)
            elif isinstance(symbol, ClassSymbol):
                NodeAndType.put_type_of_node(ctx, symbol)
            elif isinstance(symbol, VariableSymbol):  # 函数返回的是闭包函数
                if isinstance(symbol.type, FunctionSymbol):
                    return_type = symbol.type.return_type
                    NodeAndType.put_type_of_node(ctx, return_type)
                else:
                    e = CompileError("variable '%s' is not function" % symbol.name, ctx.start.line)
                    self.compile_err_list.append(e)
            elif isinstance(symbol, FunctionSymbol):
                return_type = symbol.return_type
                NodeAndType.put_type_of_node(ctx, return_type)
            else:
                raise ValueError("does not supprot now! RefResolver debug")
        elif ctx.bop is not None and ctx.bop.text in ["+", "-", "*", "/"]:
            ll = NodeAndType.get_type_of_node(ctx.expression(0))
            rr = NodeAndType.get_type_of_node(ctx.expression(1))

            if can_operate(ll) and can_operate(rr):
                NodeAndType.put_type_of_node(ctx, PrimitiveType())
            else:
                err_msg = "bad operation for %s + %s" % (ctx.expression(0).getText(), ctx.expression(1).getText())
                err_line = ctx.expression(0).start.line
                self.compile_err_list.append(CompileError(err_msg, err_line))

                NodeAndType.put_type_of_node(ctx, BadType())

        elif ctx.primary() is not None:
            # 由子节点计算自己的属性, 类型推导
            children_symbol = NodeScopeMap.get_symbol(ctx, ctx.primary().getText())
            children_type = children_symbol.type
            # children_type = NodeAndSymbol.get_symbol_of_node(ctx.primary())
            NodeAndType.put_type_of_node(ctx, children_type)
        elif ctx.bop is not None and ctx.bop.text == ".":  # 访问类
            if ctx.IDENTIFIER() is not None:   # 访问类的属性
                # TODO:难点

                variable_symbol = NodeAndType.get_type_of_node(ctx.expression(0))

                class_symbol = variable_symbol.type
                class_symbol.update_self()

                field_name = ctx.IDENTIFIER().getText()
                field_type = class_symbol.get_filed_by_name(field_name)
                if field_type is None:
                    err_msg = "no field '%s' in class '%s'" % (field_name, class_symbol.name)
                    self.compile_err_list.append(CompileError(err_msg, ctx.start.line))
                else:
                    NodeAndType.put_type_of_node(ctx, field_type)
            elif ctx.functionCall() is not None:   # 访问类的方法
                # 调用类方法就返回函数返回值类型
                function_name = ctx.functionCall().IDENTIFIER().getText()

                variable_symbol = NodeScopeMap.get_symbol(ctx, ctx.expression(0).primary().getText())
                class_symbol = variable_symbol.type

                class_symbol.update_self()
                field_type = class_symbol.get_func_by_name(function_name)
                if field_type is None:
                    err_msg = "no function '%s' in class '%s'" % (function_name, class_symbol.name)
                    self.compile_err_list.append(CompileError(err_msg, ctx.start.line))
                else:
                    NodeAndType.put_type_of_node(ctx, field_type.return_type)

        # else:
            # raise ValueError("does not support other expression")

    def exitVariableInitializer(self, ctx):
        """
        :param ctx:
        :return:
        """
        if ctx.expression() is not None:
            t = NodeAndType.get_type_of_node(ctx.expression())
            NodeAndType.put_type_of_node(ctx, t)
        else:
            raise ValueError("not support now")
