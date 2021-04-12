# coding:utf-8
"""
LL算法 https://time.geekbang.org/column/article/138385

1. 解析语法规则文件，树状结构
2. 计算first、follow集合
3. 对文本做词法解析
    3.1 构建DFA
    3.2 DFA做词法分析
4. 语法解析
    4.1 利用语法规则 匹配 词法解析好的token串，返回语法树

一类写法
add: mul ('+' mul) *
mul: pri ('*' pri) *
pri: [0-9]+

"""
from algorithm import regex


grammar_node_token_map = {
    "constant1": "",
    "constant2": "",
    "constant3": "PLUS",
    "constant4": "MUL",
    "constant5": "",
    "constant6": "INT",
    "constant7": "LPAREN",
    "constant8": "RPAREN",
}

token_grammar_node_map = {
    "PLUS": "constant3",
    "MUL": "constant4",
    "INT": "constant6",
    "LPAREN": "constant7",
    "RPAREN": "constant8"
}


class NodeType(object):
    OR = "1"
    AND = "2"

    CHAR = "3"
    RANGE = "4"   # [0-9]


class EBNFNode(object):
    def __init__(self, name, node_type, value, repeat=0):
        self.name = name
        self.node_type = node_type  # OR AND
        self.children_list = []
        # 单字节数字
        # 单字节字符
        # RANGE
        self.value = value
        self.repeat = repeat  # 0 no repeat 1 *  2 +

        first = []
        follow = []


class SampleGrammar(object):
    @staticmethod
    def expression_grammar():
        """
         * 消除了左递归的表达式语法规则：
         * expression	: equal ;
         * equal: rel equal1 ;
         * equal1	: (== | !=) rel equal1 | ε ;
         * rel	: add rel1 ;
         * rel1	: (>= | > | <= | <) add rel1 | ε ;
         * add	: mul add1 ;
         * add1	: (+ | -) mul add1 | ε ;
         * mul	: pri mul1 ;
         * mul1	: (* | /) pri mul1 | ε ;
         * pri	: ID | INT_LITERAL | LPAREN add RPAREN ;

         这个规则感觉都不用计算first集合

         目前的规则：
         add: mul add1
         add1: tmp_add1 | ε
         tmp_add1: [+-] mul add1
         mul: pri mul1
         mul1: tmp_mul1 | ε
         tmp_mul1: [*/] pri mul1
         pri: [0-9] | (add)

        :return:
        """
        # expression = EBNFNode("expression", NodeType.AND, "root")
        # equal = EBNFNode("equal", NodeType.AND, "equal")
        # equal1 = EBNFNode("equal1", NodeType.OR, "equal1")
        # rel = EBNFNode("rel", NodeType.AND, "rel")
        # rel1 = EBNFNode("rel1", NodeType.OR, "rel1")
        add = EBNFNode("add", NodeType.AND, "add")
        add1 = EBNFNode("add1", NodeType.OR, "add1")
        mul = EBNFNode("mul", NodeType.AND, "mul")
        mul1 = EBNFNode("mul1", NodeType.OR, "mul1")
        pri = EBNFNode("pri", NodeType.OR, "pri")

        # constant1 = EBNFNode("constant1", NodeType.OR, "==|!=")   # 常量字符串 == !=
        # constant2 = EBNFNode("constant2", NodeType.OR, ">= | > | <= | <")   # 常量字符串 >= | > | <= | <
        constant3 = EBNFNode("constant3", NodeType.OR, "+ | -")
        constant4 = EBNFNode("constant4", NodeType.OR, "* | /")
        constant5 = EBNFNode("constant5", NodeType.OR, "")  # ε
        constant6 = EBNFNode("constant6", NodeType.OR, "0|1|2|3|4|5|6")
        constant7 = EBNFNode("constant7", NodeType.OR, "( | )")
        constant8 = EBNFNode("constant8", NodeType.OR, "( | )")

        # # expression
        # expression.children_list.append(equal)
        #
        # # equal
        # equal.children_list = [rel, equal1]
        #
        # # equal1
        # tmp_equal1 = EBNFNode("tmp_equal1", NodeType.AND, "tmp_equal1")
        # tmp_equal1.children_list = [constant1, rel, equal1]
        # equal1.children_list = [tmp_equal1, constant5]
        #
        # # rel
        # rel.children_list = [add, rel1]
        #
        # # rel1
        # tmp_rel1 = EBNFNode("tmp_rel1", NodeType.AND, "tmp_rel1")
        # tmp_rel1.children_list = [constant2, add, rel1]
        # rel1.children_list = [tmp_rel1, constant5]

        # add和add1
        add.children_list = [mul, add1]

        tmp_add1 = EBNFNode("tmp_add1", NodeType.AND, "tmp_add1")
        tmp_add1.children_list = [constant3, mul, add1]
        add1.children_list = [tmp_add1, constant5]

        # mul
        mul.children_list = [pri, mul1]

        tmp_mul1 = EBNFNode("tmp_mul1", NodeType.AND, "tmp_mul1")
        tmp_mul1.children_list = [constant4, pri, mul1]
        mul1.children_list = [tmp_mul1, constant5]

        # pri
        tmp_pri = EBNFNode("tmp_pri", NodeType.AND, "tmp_pri")
        tmp_pri.children_list = [constant7, add, constant8]

        pri.children_list = [constant6, tmp_pri]

        return add


class AstNode(object):
    def __init__(self, value):
        """
        :param value:
        """
        self.value = value
        self.children_list = []

    def append_child(self, node):
        """
        :param node:
        :return:
        """
        self.children_list.append(node)

    def __str__(self):
        return self.value

    def dump(self, depth=0):
        """
        :return:
        """
        print("    " * depth + str(self.value))
        for i in self.children_list:
            if i is True:
                print("    " * (depth + 1) + "ε")
            else:
                i.dump(depth + 1)


class Parser(object):
    def __init__(self, grammar: EBNFNode):
        self.grammar = grammar

        # 已经计算过的节点类型
        # {"node_name1": [node_name2, node_name3]}
        self.computed_first_type = {}
        self.computed_follow_type = []   #

        self.computed_node = []  # ["node_name1", "node_name2"]

    def _calc_first(self, node):
        """
        :param node:
        :return:
        """
        first = []

        if node.name.startswith("constant"):
            return [node.name]
        elif node.name in self.computed_first_type:
            return self.computed_first_type[node.name]

        elif node.node_type == NodeType.AND:
            first_node_name = node.children_list[0].name

            if first_node_name in self.computed_first_type:
                first = self.computed_first_type[first_node_name]
            else:
                first = self._calc_first(node.children_list[0])

            self.computed_first_type[node.name] = first
            return self.computed_first_type[node.name]
        elif node.node_type == NodeType.OR:

            if node.name in self.computed_first_type:
                first = self.computed_first_type[node.name]
            else:
                for i in node.children_list:
                    node_name = i.name
                    if node_name in self.computed_first_type:
                        first.extend(self.computed_first_type[node_name])
                    else:
                        first_value = self._calc_first(i)

                        first.extend(first_value)
                        self.computed_first_type[node_name] = first_value

            self.computed_first_type[node.name] = first

            return self.computed_first_type[node.name]
        else:
            raise ValueError("should not be here")

    def calc_first(self, node):
        """
        计算first集合
        :return:
        """
        # 遍历图，怎么保证图的每一个节点都遍历到了
        # if node.name in self.computed_node:
        #     return

        for children_node in node.children_list:
            if children_node.name not in self.computed_node:
                self.computed_node.append(children_node.name)

                self.calc_first(children_node)
                self._calc_first(children_node)

    def calc_follow(self):
        pass

    def dump_first(self):
        """
        :return:
        """
        for i in self.computed_first_type:
            print(i, self.computed_first_type[i])

    def match(self, grammar: EBNFNode, token):
        """
        没有使用first && follow集合

        使用深度优先算法，存在回溯

        :param grammar:
        :param token:
        :return: False 匹配失败；AstNode
        """
        # if token.peek() is None:
        #     print(111)

        if grammar.name.startswith("constant"):  # 常量，叶子节点？
            if grammar.name == "constant5":  # TODO：这里需要特殊处理  if分支存在优先级
                return True
            elif token.peek() is None:   # 注意这里的特殊处理，if分支存在优先级
                return False
            elif grammar.name == "constant3" and token.peek().token_type == "PLUS":
                t = token.read()
                return AstNode(t)
            elif grammar.name == "constant4" and token.peek().token_type == "MUL":
                t = token.read()
                return AstNode(t)
            elif grammar.name == "constant6" and token.peek().token_type == "INT":
                t = token.read()
                return AstNode(t)
            elif grammar.name == "constant7" and token.peek().token_type == "LPAREN":
                t = token.read()
                return AstNode(t)
            elif grammar.name == "constant8" and token.peek().token_type == "RPAREN":
                t = token.read()
                return AstNode(t)
            else:
                return False

        if grammar.node_type == NodeType.OR:
            for children_grammar in grammar.children_list:
                restore = token.index
                node = self.match(children_grammar, token)

                if node is False:
                    token.index = restore  # 恢复token指针,回溯
                else:
                    ret = AstNode(grammar.name)
                    ret.append_child(node)
                    return ret
            return False
        elif grammar.node_type == NodeType.AND:
            restore = token.index

            ret = AstNode(grammar.name)

            for children_grammar in grammar.children_list:
                # print(children_grammar.value)
                node = self.match(children_grammar, token)
                if node is False:
                    token.index = restore   # 恢复token指针,调用函数会尝试其他可能
                    return False
                else:
                    ret.append_child(node)

            return ret
        else:
            raise ValueError("should not be here")

    def ll_match(self, grammar: EBNFNode, token):
        """
        :param grammar:
        :param token:
        :return:
        """

        if grammar.name.startswith("constant"):  # 常量，叶子节点？
            if grammar.name == "constant5":  # TODO：这里需要特殊处理  if分支存在优先级
                return True
            elif token.peek() is None:  # 注意这里的特殊处理，if分支存在优先级
                return False
            elif grammar.name == "constant3" and token.peek().token_type == "PLUS":
                t = token.read()
                return AstNode(t)
            elif grammar.name == "constant4" and token.peek().token_type == "MUL":
                t = token.read()
                return AstNode(t)
            elif grammar.name == "constant6" and token.peek().token_type == "INT":
                t = token.read()
                return AstNode(t)
            elif grammar.name == "constant7" and token.peek().token_type == "LPAREN":
                t = token.read()
                return AstNode(t)
            elif grammar.name == "constant8" and token.peek().token_type == "RPAREN":
                t = token.read()
                return AstNode(t)
            else:
                return False

        elif grammar.node_type == NodeType.OR:
            for children_grammar in grammar.children_list:
                first = self.computed_first_type[children_grammar.name]
                t = token.peek()

                if t is None and children_grammar.name != "constant5":
                    continue

                if children_grammar.name == "constant5" or token_grammar_node_map[t.token_type] in first:
                    node = self.ll_match(children_grammar, token)
                    ret = AstNode(grammar.name)
                    ret.append_child(node)
                    return ret

            return False
        elif grammar.node_type == NodeType.AND:
            restore = token.index

            ret = AstNode(grammar.name)

            for children_grammar in grammar.children_list:
                # print(children_grammar.value)
                node = self.ll_match(children_grammar, token)
                if node is False:
                    token.index = restore   # 恢复token指针,调用函数会尝试其他可能
                    return False
                else:
                    ret.append_child(node)

            return ret
        else:
            raise ValueError("should not be here")

    def parse(self, token):
        """
        :param token:
        :return:
        """
        ast = self.match(self.grammar, token)

        if token.peek() is not None:  # token没有消费完
            return False
        return ast

    def ll_parse(self, token):
        """
        基于递归下降的LL算法
        :param token:
        :return:
        """
        ast = self.ll_match(self.grammar, token)

        if token.peek() is not None:  # token没有消费完
            return False
        return ast


class TokenParser(object):
    def __init__(self):
        self.dfa = TokenParser.generate_dfa()
        self.index = 0   # 解析字符串的位置
        self.s = ""   # 解析字符串

    @staticmethod
    def generate_dfa():
        tree = regex.prepare_regex_4()
        nfa = regex.to_nfa(tree)
        dfa = regex.nfa2dfa(nfa)
        # print(regex.match_dfa(dfa, "11"))
        # dfa.dump()
        return dfa

    def get_token(self):
        """
        :return: 没有可匹配的token
        """
        s = self.s[self.index:]
        s_len = len(s)
        index = s_len
        while index > 0:
            state = regex.match_dfa(self.dfa, s[0: index])
            if state is False:  # 没有匹配上
                index -= 1
            else:
                self.index += index
                return state
        return False

    def tokenize(self, s):
        """
        :param s:
        :return:  False表示解析失败  ret_token_list 解析的token列表
        """
        self.s = s
        self.index = 0
        last_index = 0

        ret_token_list = []
        while True:
            last_index = self.index

            if len(self.s) == self.index:   # 字符串结尾
                break

            token = self.get_token()
            if token is False:
                return False
            else:
                # dfa.dump 查看 state和对应的token
                if str(token) == "State1['18']":  # [0-9]+
                    t = TokenElement("INT", self.s[last_index:self.index])
                    ret_token_list.append(t)
                elif str(token) in ["State2['7']", "State3['9']"]:  # + -
                    t = TokenElement("PLUS", self.s[last_index:self.index])
                    ret_token_list.append(t)
                elif str(token) in ["State4['14']", "State5['16']"]:  # * /
                    t = TokenElement("MUL", self.s[last_index:self.index])
                    ret_token_list.append(t)
                elif str(token) in ["State6['23']"]:  # (
                    t = TokenElement("LPAREN", self.s[last_index:self.index])
                    ret_token_list.append(t)
                elif str(token) in ["State7['25']"]:  # )
                    t = TokenElement("RPAREN", self.s[last_index:self.index])
                    ret_token_list.append(t)
                else:
                    raise ValueError(str(token))
        return Token(ret_token_list)


class Token(object):
    def __init__(self, tokens):
        self.tokens = tokens
        self.index = 0  # 当前消耗的token位置
        self.save_index = 0

    def peek(self):
        if self.index < len(self.tokens):
            return self.tokens[self.index]
        else:
            return None

    def read(self):
        tmp = self.tokens[self.index]
        self.index += 1
        return tmp

    def __str__(self):
        return str(self.tokens)


class TokenElement(object):
    def __init__(self, token_type, value):
        """
        :param name:
        :param value:
        """
        self.token_type = token_type
        self.value = value

    def __str__(self):
        """
        :return:
        """
        return self.value


if __name__ == "__main__":
    grammar = SampleGrammar.expression_grammar()
    p = Parser(grammar)
    p.calc_first(grammar)

    # p.dump_first()

    tp = TokenParser()
    token = tp.tokenize("1*(2+3)")

    # print(token)

    ast = p.ll_parse(token)
    # print(ast)
    if ast is False:
        print("parse fail")
    else:
        ast.dump(0)
