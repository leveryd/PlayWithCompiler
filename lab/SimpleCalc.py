# coding:utf-8
"""
https://time.geekbang.org/column/article/119891

实现简单的计算器，支持 1+2*3-5

等价EBNF
add: mul | mul (+|-)  add
mul: pri | pri (*|/) mul
pri: [0-9]+

1. 避免深度优先不解决左递归
2. 这里的结合性是有结合的，存在点问题，如 1+2+3会按照 1+(2+3) 计算
"""


class Token(object):
    def __init__(self, token_type="", token_value=""):
        self.tokenType = token_type
        self.tokenValue = token_value

    def __str__(self):
        return self.tokenType + ":" + self.tokenValue


class TokenTypes(object):
    """
    """
    MUL = "*"
    PLUS = "+"
    INT = "INT"  # 数字
    INIT = "INIT"


class NodeTypes(object):
    """

    """
    INT = "INT"
    MUL_EXP = "MUL_EXP"
    PLUS_EXP = "PLUS_EXP"


class TokensParser(object):
    def __init__(self, tokens):
        self.tokens = tokens

    def peek(self):
        return self.tokens[0]

    def read(self):
        tmp = self.tokens[0]
        self.tokens = self.tokens[1:]
        return tmp


tokens = []


def flex_parser(input):
    """
    :param input: input = "11 + 111 * 222"
    :return:
    """
    # 刚开始的状态
    current_state = TokenTypes.INIT

    i = 0

    while True:

        if i == len(input):

            for _ in tokens:
                # print(_)
                pass
            return tokens

        if current_state == TokenTypes.INIT:
            if input[i] in ["+", "-"]:  #
                current_state = TokenTypes.PLUS
                tokens.append(Token(TokenTypes.PLUS, input[i]))

                current_state = TokenTypes.INIT
            elif input[i] in ["*", "/"]:   #
                current_state = TokenTypes.MUL
                tokens.append(Token(TokenTypes.MUL, input[i]))

                current_state = TokenTypes.INIT
            elif input[i].isdigit():
                current_state = TokenTypes.INT
                tokens.append(Token(TokenTypes.INT, input[i]))

            i += 1

        elif current_state == TokenTypes.INT:
            if input[i].isdigit():
                tokens[-1].tokenValue += input[i]
                i += 1
            else:
                current_state = "INIT"


class SimpleASTNode(object):
    def __init__(self, node_type="", value=0, children="", parent=""):
        self.node_type = node_type
        self.value = value
        self.children = children
        self.parent = parent


def mul_exp(tokens):
    """
    等价的BNF
        mul: pri | pri (*|/) mul
    :param tokens:
    :return:
    """
    if tokens.peek().tokenType == TokenTypes.INT:
        current_token = tokens.read()
        assert current_token.tokenType == TokenTypes.INT   # 输入语法没错的情况下，这里根据文法肯定是 pri

        left = SimpleASTNode(node_type=NodeTypes.INT, value=int(current_token.tokenValue))
        if len(tokens.tokens) > 1 and tokens.peek().tokenType == TokenTypes.MUL:  # *和/字符 token类型都是TokenTypes.MUL
            t = tokens.read()
            right = mul_exp(tokens)
            ret_dict = {
                "node_type": NodeTypes.MUL_EXP,
                "value": t.tokenValue,
                "children": [left, right]
            }
            return SimpleASTNode(**ret_dict)
        else:
            return left


def add_exp(tokens):
    """
    等价的BNF
        add: mul | mul (+|-)  add

    :param tokens:
    :return:
    """
    mul_node = mul_exp(tokens)
    if len(tokens.tokens) > 1 and tokens.peek().tokenType == TokenTypes.PLUS:  # +和-字符 token类型都是TokenTypes.PLUS
        t = tokens.read()
        right = add_exp(tokens)
        ret_dict = {
            "node_type": NodeTypes.PLUS_EXP,
            "value": t.tokenValue,
            "children": [mul_node, right]
        }
        return SimpleASTNode(**ret_dict)
    return mul_node


def parse_ast(tokens):
    """
    从tokens打印AST树
    :param tokens:
    :return:
    """
    tp = TokensParser(tokens)
    x = add_exp(tp)
    return x


def execute(ast):
    """
    :param ast: 由解析好的ast树计算值
    :return:
    """
    if ast.node_type == NodeTypes.INT:
        return ast.value
    elif ast.node_type == NodeTypes.PLUS_EXP:
        left = execute(ast.children[0])
        right = execute(ast.children[1])
        if ast.value == "+":
            return left + right
        else:
            return left - right
    elif ast.node_type == NodeTypes.MUL_EXP:
        left = execute(ast.children[0])
        right = execute(ast.children[1])
        if ast.value == "*":
            return left * right
        else:
            return left / right


if __name__ == "__main__":
    tokens = flex_parser("2+3*4")
    ast = parse_ast(tokens)
    print(execute(ast))
