"""
规约算法 解析 四则运算表达式 语法树
https://time.geekbang.org/column/article/139628

1. 计算NFA
2. 计算follow

1. 词法分析 （省略）
2. 语法分析
    * 尝试规约
    * 尝试移进
"""

rules = {
    'E': ['A'],
    'A': ['A+M', 'M'],
    'M': ['M*P', 'P'],
    'P': ['(E)', 'N'],
    # 'N': [str(i) for i in range(10)],
}

NFA = {

}

follow = {
    'E': [')','$'],
    'A': ['+', '$'],
    'M': ['*', '$'],
    'P': ['$'],
    'N': ['$']
}

class Lexer(object):
    def __init__(self, s):
        self.s = s
        self.pos = 0

    def read(self):
        return self.s[self.pos]

    def peek(self):
        ret = self.s[self.pos]
        self.pos += 1
        return ret


def reduce(token, next_token):



if __name__ == "__main__":
    s = Lexer("N+N")

    while True:


