# coding:utf-8
"""
Python实现 https://time.geekbang.org/column/article/154438 课程内容

Python3环境，依赖：pip3 install llvmlite

llvm Python接口参考资料：
    https://github.com/numba/llvmlite/blob/master/llvmlite/tests
    https://github.com/numba/llvmlite/blob/master/examples
"""
from __future__ import print_function

import os
import argparse
from ctypes import CFUNCTYPE, c_int

import llvmlite.ir as ll
import llvmlite.binding as llvm


# 初始化与目标硬件平台有关的设置
llvm.initialize()
llvm.initialize_native_target()
llvm.initialize_native_asmprinter()


generate_ll_file = "test.ll"


def generate_sum_module():
    """
    实现下面的C函数

    int sum(int a,int b){
        return a+b;
    }
    :return:
    """
    # 1.生成一个module
    module = ll.Module(name="sum")

    # 2.定义函数类型
    function_type = ll.FunctionType(ll.IntType(32), [ll.IntType(32), ll.IntType(32)])

    # 3.创建函数和一个基本块

    func = ll.Function(module, function_type, name="sum")

    bb_entry = func.append_basic_block()

    # 4.生成a+b表达式的IR，插入到基本块中
    builder = ll.IRBuilder()
    builder.position_at_end(bb_entry)

    ret = builder.add(func.args[0], func.args[1])  # 对应汇编add或者leal指令，实现加和

    # 5.获取返回值
    builder.ret(ret)

    mod_str = str(module)
    with open(generate_ll_file, "w") as f:
        f.write(mod_str)
    return llvm.parse_assembly(mod_str)


def generate_if_module():
    """
    int fun_ifstmt(int a)
      if (a < 2)
        return 1;
      else
        return 0；
    }

    一般CFG会要求有两个特殊的块：入口块（Entry Block）和退出块（Exit Block）。这样的话，CFG就是一个有根的图（Rooted Directed Graph），便于执行某些分析和优化算法。

    所以下面的设计虽然功能可以实现，但是不是符合一般的CFG形态。
    :return:
    """
    # 1.生成一个module
    module = ll.Module(name="if")

    # 2.定义函数类型
    function_type = ll.FunctionType(ll.IntType(32), [ll.IntType(32)])

    # 3.创建函数和一个基本块

    func = ll.Function(module, function_type, name="if")

    bb_entry = func.append_basic_block()
    bb_then = func.append_basic_block()
    bb_else = func.append_basic_block()
    # bb_merge = func.append_basic_block()

    builder = ll.IRBuilder()
    # 4. 生成then模块
    builder.position_at_end(bb_then)

    # return 1 表达式
    constant_int_1 = ll.Constant(ll.IntType(32), 1)
    builder.ret(constant_int_1)

    # 5. 生成else模块
    builder.position_at_end(bb_else)

    # return 0 表达式
    constant_int_2 = ll.Constant(ll.IntType(32), 0)   # ll.Constant(func.args[0].type, 2)
    builder.ret(constant_int_2)

    # 6.生成if模块，插入到基本块中
    builder.position_at_end(bb_entry)

    # if a < 2 {} else {} 的表达式
    constant_int = ll.Constant(ll.IntType(32), 2)
    cond = builder.icmp_signed("<", func.args[0], constant_int)
    builder.cbranch(cond, bb_then, bb_else)

    # 5.获取返回值
    # builder.ret(ret)

    mod_str = str(module)
    with open(generate_ll_file, "w") as f:
        f.write(mod_str)
    return llvm.parse_assembly(mod_str)


def generate_if_module_v2():
    """
    int fun_ifstmt(int a)
      if (a < 2)
        return 1;
      else
        return 0;
    }

    相比于v1，变化是多了merge块，使用phi指令
    :return:
    """
    # 1.生成一个module
    module = ll.Module(name="if")

    # 2.定义函数类型
    function_type = ll.FunctionType(ll.IntType(32), [ll.IntType(32)])

    # 3.创建函数和一个基本块

    func = ll.Function(module, function_type, name="if")

    bb_entry = func.append_basic_block()
    bb_then = func.append_basic_block()
    bb_else = func.append_basic_block()
    bb_merge = func.append_basic_block()

    builder = ll.IRBuilder()

    # 4. 生成then模块
    builder.position_at_end(bb_then)
    builder.branch(bb_merge)   # 无条件跳转到bb_merge模块
    ThenValue = ll.Constant(func.args[0].type, 1)

    # 5. 生成else模块
    builder.position_at_end(bb_else)
    builder.branch(bb_merge)    # 无条件跳转到bb_merge模块
    ElseValue = ll.Constant(func.args[0].type, 0)

    # 6. 生成if模块，插入到基本块中
    builder.position_at_end(bb_entry)

    # if a > 2 {} else {} 的表达式
    constant_int = ll.Constant(func.args[0].type, 2)
    cond = builder.icmp_signed("<", func.args[0], constant_int)
    builder.cbranch(cond, bb_then, bb_else)

    # 5. 生成merge模块
    builder.position_at_end(bb_merge)
    function_return = builder.phi(ll.IntType(32))
    function_return.add_incoming(ThenValue, bb_then)
    function_return.add_incoming(ElseValue, bb_else)

    builder.ret(function_return)

    mod_str = str(module)
    with open(generate_ll_file, "w") as f:
        f.write(mod_str)
    return llvm.parse_assembly(mod_str)


def generate_if_module_v3():
    """
    int fun_ifstmt(int a)
      int ret;
      if (a < 2)
        ret = 1;
      else
        ret = 0;
      return ret;
    }

    相比于v2的变化：使用变量存储结果
    :return:
    """
    # 1.生成一个module
    module = ll.Module(name="if")

    # 2.定义函数类型
    function_type = ll.FunctionType(ll.IntType(32), [ll.IntType(32)])

    # 3.创建函数和一个基本块
    func = ll.Function(module, function_type, name="if")

    bb_entry = func.append_basic_block()
    bb_then = func.append_basic_block()
    bb_else = func.append_basic_block()
    bb_merge = func.append_basic_block()

    builder = ll.IRBuilder()

    # 4. 生成if模块，插入到基本块中
    builder.position_at_end(bb_entry)
    ret = builder.alloca(ll.IntType(32), name="ret")   # ret是一个地址，相当于指针

    # if a > 2 {} else {} 的表达式
    constant_int = ll.Constant(func.args[0].type, 2)
    cond = builder.icmp_signed("<", func.args[0], constant_int)
    builder.cbranch(cond, bb_then, bb_else)

    # 5. 生成then模块
    builder.position_at_end(bb_then)
    then_value = ll.Constant(func.args[0].type, 1)
    builder.store(then_value, ret)
    builder.branch(bb_merge)    # 无条件跳转到bb_merge模块

    # 6. 生成else模块
    builder.position_at_end(bb_else)
    else_value = ll.Constant(func.args[0].type, 0)
    builder.store(else_value, ret)
    builder.branch(bb_merge)    # 无条件跳转到bb_merge模块

    # 7. 生成merge模块
    builder.position_at_end(bb_merge)
    builder.ret(builder.load(ret))

    mod_str = str(module)
    with open(generate_ll_file, "w") as f:
        f.write(mod_str)
    return llvm.parse_assembly(mod_str)


def compile_and_run_if(module, int_input):
    """
    :param module:
    :param int_input:
    :return:
    """
    # 还不明白这一行的意思
    target_machine = llvm.Target.from_default_triple().create_target_machine()

    with llvm.create_mcjit_compiler(module, target_machine) as ee:
        ee.finalize_object()
        cfptr = ee.get_function_address("if")

        # 打印汇编代码
        # print(target_machine.emit_assembly(module))

        func = CFUNCTYPE(c_int, c_int)(cfptr)
        res = func(int_input)

        return res


def for_function():
    """
    int for_function(int start,int end){
        int i=start;
        int sum=0;
        for(;i<=end;i++){
            sum=sum+i;
        }
        return sum;
    }
    :return:
    """
    pass


def build():
    """
    生成目标模块
    :return:
    """
    pass


def call_external_function():
    """
    调用foo.c的外部函数foo
    void foo(int a){
        printf("in foo: %d\n",a);
    }

    运行：make run1

        此函数会生成test.s汇编文件，Makefile中和foo.c文件一起组成可执行文件。

    奇怪的现象：
    1. ll.Block() 似乎不会生成块
    :return:
    """
    # 1.生成一个module
    module = ll.Module(name="call_external_function")

    # 2.定义函数类型
    function_type = ll.FunctionType(ll.IntType(32), [ll.IntType(32)])

    # 3.创建main函数块
    main_function_type = ll.FunctionType(ll.IntType(32), [ll.IntType(32)])
    main_func = ll.Function(module, main_function_type, name="main")

    bb_entry = main_func.append_basic_block()

    # function = ll.NamedValue(module, type=function_type, name="x")
    # llvm.load_library_permanently("/tmp/foo.so")

    # 4.插入函数调用
    builder = ll.IRBuilder()
    builder.position_at_end(bb_entry)

    # func = CFUNCTYPE(c_int, c_int)(foo_function)   # 失败的尝试
    # func = ll.GlobalVariable(module, function_type, 'func')  # 失败的尝试
    func = ll.Function(module, function_type, "foo")

    builder = ll.IRBuilder(bb_entry)

    a = builder.function.args[0]
    builder.call(func, [a])
    # builder.call(func, [ll.Constant(ll.IntType(32), 1)])

    # 5.main函数return
    builder.position_at_end(bb_entry)
    builder.ret(ll.Constant(ll.IntType(32), 1))

    # print(str(module))
    x_module = llvm.parse_assembly(str(module))

    # 还不明白这一行的意思
    target_machine = llvm.Target.from_default_triple().create_target_machine()

    with llvm.create_mcjit_compiler(x_module, target_machine) as ee:
        ee.finalize_object()

        # 保存汇编代码
        with open("main.s", "w") as f:
            f.write(target_machine.emit_assembly(x_module))

    return module


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='llvm usage demo.')

    parser.add_argument('--sum', default=False, help='call sum function which we create by llvm,ld main.c test1.ll', action="store_true")
    parser.add_argument('--ifv1', default=False, help='if statement implement,version 1', action="store_true")
    parser.add_argument('--ifv2', default=False, help='if statement implement,version 2', action="store_true")
    parser.add_argument('--ifv3', default=False, help='if statement implement,version 3', action="store_true")
    parser.add_argument('--foo', default=False, help='call external "foo" function', action="store_true")

    args = parser.parse_args()
    if args.sum is True:
        generate_sum_module()

        os.system("make run")
        os.system("make clean 2>/dev/null")
    elif args.ifv1 is True:
        module = generate_if_module()
        assert(compile_and_run_if(module, 1) == 1)

        module = generate_if_module()
        assert(compile_and_run_if(module, 2) == 0)

        module = generate_if_module()
        assert (compile_and_run_if(module, 3) == 0)
    elif args.ifv2 is True:
        module = generate_if_module_v2()
        assert(compile_and_run_if(module, 1) == 1)

        module = generate_if_module_v2()
        assert(compile_and_run_if(module, 2) == 0)

        module = generate_if_module_v2()
        assert (compile_and_run_if(module, 3) == 0)
    elif args.ifv3 is True:
        module = generate_if_module_v3()
        assert(compile_and_run_if(module, 1) == 1)

        module = generate_if_module_v3()
        assert(compile_and_run_if(module, 2) == 0)

        module = generate_if_module_v3()
        assert (compile_and_run_if(module, 3) == 0)
    elif args.foo is True:
        call_external_function()
        os.system("make run_1 2>/dev/null")
        os.system("make clean 2>/dev/null")
    else:
        print("usage: python3 test1.py -h")
