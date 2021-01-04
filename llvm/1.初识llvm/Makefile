build:  # 仅在mac下测试过
	@clang -S -O2 test.ll -o test.s
	@clang -S -O2 main.c -o main.s
	@as test.s -o test.o
	@as main.s -o main.o
	@# 非mac系统需要修改/usr/lib/libSystem.B.dylib路径为libc库路径
	@ld main.o test.o /usr/lib/libSystem.B.dylib -o a.out
	@# @ld test.o /usr/lib/libSystem.B.dylib -o a.out

run: build
	@./a.out

#调用
run_1:
	@clang -S -O2 foo.c -o foo.s

	@as main.s -o main.o
	@as foo.s -o foo.o
	@ld main.o foo.o /usr/lib/libSystem.B.dylib -o a.out
	@./a.out

clean:
	@rm a.out main.o main.s test.o test.s test.ll foo.o foo.so foo.s