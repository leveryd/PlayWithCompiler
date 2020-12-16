#!/usr/bin/python2
# coding:utf-8
from antlr4 import *
from dist.PlayScriptLexer import PlayScriptLexer
from dist.PlayScriptParser import PlayScriptParser
from dist.PlayScriptVisitor import PlayScriptVisitor


vars_list = {}


class PlayVisitor(PlayScriptVisitor):
    def visitIntegerLiteral(self, ctx):
        return int(ctx.getText())

    def visitProg(self, ctx):
        return self.visitBlockStatements(ctx.blockStatements())

    def visitBlockStatements(self, ctx):
        ret = None
        for i in ctx.blockStatement():
            ret = self.visitBlockStatement(i)
        return ret

    def visitBlockStatement(self, ctx):
        if ctx.variableDeclarators() is not None:
            return self.visitVariableDeclarators(ctx.variableDeclarators())
        else:
            return self.visitStatement(ctx.statement())

    def visitVariableDeclarators(self, ctx):
        # var_type = self.visitTypeType(ctx.typeType())   # 暂时所有变量全部当作数字类型处理
        for i in ctx.variableDeclarator():
            self.visitVariableDeclarator(i)

    def visitVariableDeclarator(self, ctx):
        """
        目前将所有变量全部存储在vars_list
        :param ctx:
        :return:
        """
        if ctx.variableInitializer() is not None:
            v = self.visitExpression(ctx.variableInitializer().expression())
        else:
            v = 0
        k = ctx.variableDeclaratorId().getText()
        vars_list[k] = v

    def visitTypeType(self, ctx):
        return ctx.primitiveType().getText()

    def visitStatement(self, ctx):
        return self.visitExpression(ctx.statementExpression)

    def visitExpression(self, ctx):
        if ctx.primary() is not None:
            return self.visitPrimary(ctx.primary())
        elif ctx.bop is not None and ctx.bop.text in ["+", "-", "*", "/"]:
            ll = int(self.visit(ctx.expression(0)))   # 暂时全部当作数字处理
            rr = int(self.visit(ctx.expression(1)))
            return eval("%d%s%d" % (ll, ctx.bop.text, rr))
        elif ctx.bop is not None and ctx.bop.text == "=":
            ll = ctx.expression(0).getText()
            rr = self.visit(ctx.expression(1))
            vars_list[ll] = rr
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
            return vars_list[ctx.getText()]

    def visitFunctionCall(self, ctx):
        """
        :param ctx:
        :return:
        """
        if ctx.IDENTIFIER() is not None:
            if ctx.IDENTIFIER().getText() == "snoopy_print":   # 内置的函数
                ret = self.visitExpressionList(ctx.expressionList())
                if len(ret) == 1:
                    print(ret[0])
                else:
                    print(tuple(ret))

    def visitExpressionList(self, ctx):
        """
        :param ctx:
        :return:
        """
        ret = []
        for i in ctx.expression():
            ret.append(self.visitExpression(i))
        return ret


def main(line):
    input_stream = InputStream(line)

    # lexing
    lexer = PlayScriptLexer(input_stream)
    stream = CommonTokenStream(lexer)

    # parsing
    parser = PlayScriptParser(stream)
    tree = parser.prog()

    # use customized visitor to traverse AST
    visitor = PlayVisitor()
    return visitor.visit(tree)


if __name__ == '__main__':
    main("int a=2*3+1;a=a+3*2;int b=1+2;snoopy_print(a, b);")
