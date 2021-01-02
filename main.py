#!/usr/bin/python3
# coding:utf-8
from antlr4 import *
from dist.PlayScriptLexer import PlayScriptLexer
from dist.PlayScriptParser import PlayScriptParser
from src.ScanScopes import ScanScopes
from src.PlayVisitor import PlayVisitor
from src.TypeResolver import TypeResolver
from src.TypeChecker import TypeChecker
from src.RefResolver import RefResolver


def main(line):
    input_stream = InputStream(line)

    # lexing
    lexer = PlayScriptLexer(input_stream)
    stream = CommonTokenStream(lexer)

    # parsing
    parser = PlayScriptParser(stream)
    tree = parser.prog()

    # semantic analysis
    printer = ScanScopes(tree)
    walker = ParseTreeWalker()
    walker.walk(printer, tree)

    # I属性解析
    type_resolver = TypeResolver(tree)
    walker = ParseTreeWalker()
    walker.walk(type_resolver, tree)

    # S属性解析、类型推导
    ref_resolver = RefResolver(tree)
    walker = ParseTreeWalker()
    walker.walk(ref_resolver, tree)

    # 类型检查
    type_checker = TypeChecker(tree)
    walker = ParseTreeWalker()
    walker.walk(type_checker, tree)

    compile_err_list = type_checker.compile_error_list
    compile_err_list.extend(type_resolver.compile_error_list)
    compile_err_list.extend(ref_resolver.compile_err_list)
    if len(compile_err_list) != 0:
        print("compile error,details as below:\n")
        for compile_error in compile_err_list:
            print("    line %s: %s" % (compile_error.err_line, compile_error.err_msg))
        return False

    # 闭包分析
    # for k, v in NodeScopeMap.node_scope_list:
    #     for symbol in v.symbol_list:
    #         if isinstance(symbol, FunctionSymbol):
    #             tmp = symbol.compute_needed_symbols()
    #             print(tmp)

    # use customized visitor to traverse AST
    visitor = PlayVisitor()
    return visitor.visit(tree)


def unittest():
    import os
    for i in os.listdir("tests"):
        if i.endswith(".play"):
            file_path = "tests/" + i
            print(file_path)
            with open(file_path, "r") as f:
                s = f.read()
            main(s)


if __name__ == '__main__':
    # main("{int a=2*3+1;a=a+3*2;int b=1+2;snoopy_print(a, b);} {int a=2;}")
    # main("{int a=2;{int b=2;{int c=2;}}snoopy_print(b);} {}")
    # main("{int a=2;{int a=3;snoopy_print(a);}snoopy_print(a);}")
    # main("{int a=2;{a=3;int b=4;snoopy_print(a);}snoopy_print(a);snoopy_print(b);}")
    # main("snoopy_print(2+3);")
    # main("{int x(int a){snoopy_print(a);}x(3);}")

    # unittest()

    with open("tests/extends.play", "r") as f:
        script = f.read()
    main(script)

    # x = NodeScopeMap.node_scope_list
    # print(x)
