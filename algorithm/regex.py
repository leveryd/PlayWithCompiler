# coding:utf-8
"""
NFA/DFA实现正则表达式
https://time.geekbang.org/column/article/137286
"""
import copy
import string


MATCH = True
CONTINUE = 3
NO_MATCH = False
ALL_END = 1


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


def parse_1(payload):
    """
    :param payload: [0-9a-z]
    :return:
    """
    i = 0
    record = {"start": None, "end": None}
    value_list = []
    state = "BEGIN"  # BEGIN ANALYSE_START ANALYSE_ING ANALYSE_END END
    while True:  # 状态机解析 [a-z0-9] 字符串
        if state == "BEGIN":
            state = "ANALYSE_START"
        elif state == "ANALYSE_START":
            if payload[i] == "]":
                state = "END"
            else:
                record["start"] = payload[i]
                state = "ANALYSE_ING"
        elif state == "ANALYSE_ING":
            assert payload[i] == "-"
            state = "ANALYSE_END"
        elif state == "ANALYSE_END":
            record["end"] = payload[i]
            # 解析[]代表的值集合
            for _ in range(ord(record["start"]), ord(record["end"]) + 1):
                value_list.append(chr(_))

            state = "ANALYSE_START"
        elif state == "END":
            break
        else:
            raise ValueError("bad state")
        i += 1

    return value_list


class State(object):
    index = 0

    def __init__(self, value):
        self.name = str(State.index)
        State.index += 1

        self.value = value   # 只有三个类型：EBNFNode、State("begin")、State("end")
        self.next_state_list = []

    def append_state(self, state):
        self.next_state_list.append(state)

    def dump(self, depth=0):
        print(' ' * depth * 3 + ' %s_%s' % (self.name, str(self)))
        for i in range(0, len(self.next_state_list)):
            self.next_state_list[i].dump(depth + 1)

    def match(self, char):
        """
        返回char单字节字符是否满足当前的state
        :param char:
        :return:
        """
        if not isinstance(self.value, EBNFNode):
            pass
        else:
            if self.value.node_type == NodeType.CHAR:
                return char == self.value.value
            if self.value.node_type == NodeType.RANGE:
                if char in parse_1(self.value.value):
                    return True
                else:
                    return False

    def __str__(self):
        if isinstance(self.value, EBNFNode):
            v = self.value
            return v.value
        else:
            return self.value


class DFAState(object):
    state_dfa_map_list = []  # 所有状态集的集合S和对象映射 [[状态集1，DFAState对象1],[状态集2，DFAState对象2]]
    dfa_state_list = []   # 所有状态集的集合S
    index = 0

    def __init__(self, s):
        self.next = {}    # {"输入字符"：下一个状态集}
        self.nfa_state_collection = s   # 当前的状态集合，包含多个NFA状态
        self.name = str(DFAState.index)

    @classmethod
    def new(cls, s):
        """
        :param s:
        :return:
        """
        for i in cls.state_dfa_map_list:
            if cls.cmp(i[0], s):
                return i[1]

        dfa_state = DFAState(s)
        cls.state_dfa_map_list.append([s, dfa_state])
        cls.index += 1

        return dfa_state

    @classmethod
    def dump(cls):
        """
        :return:
        """
        for i in cls.state_dfa_map_list:
            self = i[1]

            state_chars_map = {}

            for k in self.next:
                v = self.next[k]
                if v in state_chars_map:
                    state_chars_map[v].append(k)
                else:
                    state_chars_map[v] = [k]

            print(self)
            for k in state_chars_map:
                v = state_chars_map[k]
                print("   %s -> %s" % (str(v), k))

    @classmethod
    def cmp(cls, nfa_state_collection_1, nfa_state_collection_2):
        if cls.get_nfa_state_collection_name(nfa_state_collection_1) == cls.get_nfa_state_collection_name(nfa_state_collection_2):
            return True
        # print(str(set(nfa_name_list_1)), str(set(nfa_name_list_2)))
        return False

    @classmethod
    def is_in_state_list(cls, dfa_state):
        """
        :param dfa_state:
        :return:
        """
        for i in cls.dfa_state_list:
            if cls.cmp(i.nfa_state_collection, dfa_state.nfa_state_collection):
                return True
        return False

    @classmethod
    def is_in_state_list_2(cls, nfa_state_collection):
        """
        :param nfa_state_collection:
        :return:
        """
        for i in cls.dfa_state_list:
            if cls.cmp(i.nfa_state_collection, nfa_state_collection):
                return True
        return False

    @classmethod
    def get_nfa_state_collection_name(cls, nfa_state_collection):
        """
        :param nfa_state_collection:
        :return:
        """
        nfa_name_list = [i.name for i in nfa_state_collection]
        return str(list(set(nfa_name_list)))

    def __str__(self):
        nfa_name_list = [i.name for i in self.nfa_state_collection]

        return str("State%s%s" % (self.name, nfa_name_list))


def prepare_regex():
    """
    int|[a-zA-Z][A-Za-Z0-9]*|[0-9]+
    :return:
    """
    root_node = EBNFNode("root", NodeType.OR, "root")

    children_node_1 = EBNFNode("int", NodeType.AND, "int")

    children_node_1.children_list.append(EBNFNode("i", NodeType.CHAR, 'i'))
    children_node_1.children_list.append(EBNFNode("n", NodeType.CHAR, 'n'))
    children_node_1.children_list.append(EBNFNode("t", NodeType.CHAR, 't'))
    root_node.children_list.append(children_node_1)

    children_node_2 = EBNFNode("[a-zA-Z][A-Za-Z0-9]*", NodeType.AND, "[a-zA-Z][A-Za-Z0-9]*")

    children_node_21 = EBNFNode("[a-zA-Z]", NodeType.RANGE, "[a-zA-Z]", 0)
    children_node_2.children_list.append(children_node_21)

    children_node_22 = EBNFNode("[A-Za-Z0-9]*", NodeType.RANGE, "[A-Za-z0-9]*", 1)
    children_node_2.children_list.append(children_node_22)

    root_node.children_list.append(children_node_2)

    children_node_3 = EBNFNode("[0-9]+", NodeType.RANGE, "[0-9]+", 1)
    root_node.children_list.append(children_node_3)

    return root_node


def prepare_regex_4():
    """
    [()]|==|!=|(>=|<=)|(+|-)|[0-9]+

    暂不支持 [+-]|[*/]|[0-9]+

    +|-|*|/|[0-9]+|(|)
    :return:
    """
    root_node = EBNFNode("root", NodeType.OR, "root")

    children_node_1 = EBNFNode("+-", NodeType.OR, "+-")

    children_node_1.children_list.append(EBNFNode("+", NodeType.CHAR, '+'))
    children_node_1.children_list.append(EBNFNode("-", NodeType.CHAR, '-'))
    root_node.children_list.append(children_node_1)

    children_node_2 = EBNFNode("*/", NodeType.OR, "*/")

    children_node_2.children_list.append(EBNFNode("*", NodeType.CHAR, '*'))
    children_node_2.children_list.append(EBNFNode("/", NodeType.CHAR, '/'))
    root_node.children_list.append(children_node_2)

    children_node_3 = EBNFNode("[0-9]+", NodeType.RANGE, "[0-9]+", 1)
    root_node.children_list.append(children_node_3)

    children_node_4 = EBNFNode("()", NodeType.OR, "()")

    children_node_4.children_list.append(EBNFNode("(", NodeType.CHAR, '('))
    children_node_4.children_list.append(EBNFNode(")", NodeType.CHAR, ')'))
    root_node.children_list.append(children_node_4)

    # # +|-|*|/|[0-9]+
    # root_node.children_list = [
    #     EBNFNode("+", NodeType.CHAR, '+'),
    #     EBNFNode("-", NodeType.CHAR, '-'),
    #     EBNFNode("*", NodeType.CHAR, '*'),
    #     EBNFNode("/", NodeType.CHAR, '/'),
    #     EBNFNode("[0-9]+", NodeType.RANGE, "[0-9]+", 1)
    # ]
    return root_node


def prepare_regex_3():
    """
    a[a-zA-Z0-9]*bc，也就是以a开头，bc结尾，中间可以是任何字母或数字
    :return:
    """
    root_node = EBNFNode("root", NodeType.AND, "root")

    root_node.children_list.append(EBNFNode("a", NodeType.CHAR, 'a'))
    root_node.children_list.append(EBNFNode("[a-zA-Z0-9]*", NodeType.RANGE, "[a-zA-Z0-9]*", 2))
    root_node.children_list.append(EBNFNode("b", NodeType.CHAR, 'b'))
    root_node.children_list.append(EBNFNode("c", NodeType.CHAR, 'c'))

    return root_node


def prepare_regex_2():
    """
    int|[0-9a-zA-Z]
    :return:
    """
    root_node = EBNFNode("root", NodeType.OR, "root")

    children_node_1 = EBNFNode("int", NodeType.AND, "int")

    children_node_1.children_list.append(EBNFNode("i", NodeType.CHAR, 'i'))
    children_node_1.children_list.append(EBNFNode("n", NodeType.CHAR, 'n'))
    children_node_1.children_list.append(EBNFNode("t", NodeType.CHAR, 't'))
    root_node.children_list.append(children_node_1)

    # for i in range(0, 9):
    #     tmp_node = EBNFNode("", NodeType.DIGIT, i)
    #     children_node_1.children_list.append(tmp_node)

    #
    children_node_2 = EBNFNode("[0-9a-zA-Z]", NodeType.RANGE, "[0-9a-zA-Z]", 0)
    root_node.children_list.append(children_node_2)

    return root_node


def prepare_regex_1():
    """
    int|ab|ib
    :return:
    """
    root_node = EBNFNode("root", NodeType.OR, "root")

    children_node_1 = EBNFNode("int", NodeType.AND, "int")

    children_node_1.children_list.append(EBNFNode("i", NodeType.CHAR, 'i'))
    children_node_1.children_list.append(EBNFNode("n", NodeType.CHAR, 'n'))
    children_node_1.children_list.append(EBNFNode("t", NodeType.CHAR, 't'))
    root_node.children_list.append(children_node_1)

    children_node_2 = EBNFNode("ab", NodeType.AND, "ab")

    children_node_2.children_list.append(EBNFNode("a", NodeType.CHAR, 'a'))
    children_node_2.children_list.append(EBNFNode("b", NodeType.CHAR, 'b'))
    root_node.children_list.append(children_node_2)

    children_node_3 = EBNFNode("ib", NodeType.AND, "ib")

    children_node_3.children_list.append(EBNFNode("i", NodeType.CHAR, 'a'))
    children_node_3.children_list.append(EBNFNode("b", NodeType.CHAR, 'b'))
    root_node.children_list.append(children_node_3)

    return root_node


def to_nfa(ebnf_node_tree: EBNFNode):
    """
    :param ebnf_node_tree:
    :return:
    """
    begin_state = State("begin")
    if ebnf_node_tree.node_type == NodeType.AND:
        for i in range(0, len(ebnf_node_tree.children_list)):
            current_state = to_nfa(ebnf_node_tree.children_list[i])

            # 链表结构，向后插入数据，时间复杂度O(n)
            if i == 0:
                begin_state.next_state_list.append(current_state)
            else:
                c = begin_state
                while True:
                    if len(c.next_state_list) == 0:
                        c.next_state_list.append(current_state)
                        break
                    else:
                        c = c.next_state_list[0]

        return begin_state.next_state_list[0]
    elif ebnf_node_tree.node_type == NodeType.OR:
        tmp_begin_state = State("begin")
        end_state = State("end")
        for ebnf_node in ebnf_node_tree.children_list:
            tmp_state = to_nfa(ebnf_node)

            # 这里暂时认为是单链，没有分叉
            # 在链的末尾加上end标志
            c = tmp_state
            while True:
                if len(c.next_state_list) == 0:
                    c.next_state_list.append(end_state)
                    break
                else:
                    c = c.next_state_list[0]

            tmp_begin_state.next_state_list.append(copy.copy(tmp_state))

        return tmp_begin_state
    elif ebnf_node_tree.node_type == NodeType.CHAR:
        return State(ebnf_node_tree)
    elif ebnf_node_tree.node_type == NodeType.RANGE:
        return State(ebnf_node_tree)
    else:
        return begin_state


def should_continue(user_input, index, state):
    """
    无法继续匹配的三种情况
        1. 到达了字符串末尾，但是链还没有走完
        2. 链走完了，但是字符串还没有结束
        3. 链和字符串都到了末尾
    :param user_input:
    :param index:
    :param state:
    :return: 1 （1、2），2（3）, 3（continue）
    """
    user_input_over = (index + 1 == len(user_input))
    path_over = (len(state.next_state_list) == 0 or state.next_state_list[0].value == "end")

    if path_over and user_input_over:
        if state.match(user_input[index]):
            return MATCH
        else:
            return NO_MATCH
    elif not (path_over or user_input_over):
        if state.match(user_input[index]):
            return CONTINUE
        else:
            return NO_MATCH
    elif not path_over and user_input_over:
        return NO_MATCH
    elif path_over and not user_input_over:
        if isinstance(state.value, EBNFNode) and state.value.node_type == NodeType.RANGE:
            try:
                if not state.match(user_input[index]):
                    return NO_MATCH
                elif state.value.repeat == 0:
                    return NO_MATCH
                else:
                    return CONTINUE
            except:
                pass
        else:
            return NO_MATCH
    else:
        raise ValueError("bad switch")


def match_nfa(state, user_input, index=0):
    """
    :param state: State("begin")  State("end") State(EBNFNode)
    :param user_input:
    :param index:
    :return:
    """
    action = should_continue(user_input, index, state)

    if isinstance(state.value, str):  # State("begin") 和 State("end")
        if state.value == "begin":
            children_list = state.next_state_list

            for children in children_list:
                ret = match_nfa(children, user_input, index)
                if ret is True:  # 匹配成功
                    return True
        elif state.value == "end":
            pass

    elif state.value.node_type == NodeType.CHAR:
        if action == CONTINUE:  # 链没有走完，字符串也没有到结尾
            return match_nfa(state.next_state_list[0], user_input, index + 1)
        else:
            return action

    elif state.value.node_type == NodeType.RANGE:  # 假设目前全部都是 [a-z]* 贪婪匹配
        if action == NO_MATCH:
            if state.value.repeat in [0, 1]:   # [a-z] [a-z]+
                return False
            else:
                return match_nfa(state.next_state_list[0], user_input, index)
        else:  # 匹配上了 或者 可以往后走时
            if index + 1 == len(user_input):   # 这里有可能到了用户输入的末端
                return True

            if state.value.repeat == 0:  # [a-z]  只命中一次
                return match_nfa(state.next_state_list[0], user_input, index + 1)
            elif state.value.repeat == 1:  # [a-z]+ 至少一次命中
                tmp_state = copy.copy(state)
                tmp_state.value.repeat = 2  # 变成 [a-z]*
                ret = match_nfa(tmp_state, user_input, index + 1)
                if ret is True:
                    return True
                else:
                    if len(state.next_state_list) == 0:
                        return False
                    else:
                        return match_nfa(state.next_state_list[0], user_input, index)
            else:  # [a-z]*
                ret = match_nfa(state, user_input, index + 1)  # 尝试贪婪匹配
                if ret is True:
                    return True
                else:
                    if len(state.next_state_list) == 0:
                        return False
                    else:
                        return match_nfa(state.next_state_list[0], user_input, index)
    else:
        raise ValueError("bad state")
    # 所有路径都走不通时，返回上一个字符匹配
    return False


def nfa2dfa(nfa):
    """
    :param nfa:
    :return:
    """
    to_handle_state_list = []  # 待处理栈

    begin_nfa_state = nfa
    assert begin_nfa_state.value == "begin"

    # 计算s0，即状态0的ε闭包
    begin_dfa_state = DFAState.new([begin_nfa_state])

    # 把s0压入待处理栈
    to_handle_state_list.append(begin_dfa_state.nfa_state_collection)

    # 把s0加入所有状态集的集合S
    DFAState.dfa_state_list.append(begin_dfa_state)

    while True:  # 待处理栈内还有未处理的状态集
        if len(to_handle_state_list) == 0:
            break

        state = to_handle_state_list.pop()

        # copy_to_handle_state_list = copy.copy(to_handle_state_list)
        # for state in copy_to_handle_state_list:  # 针对栈里的每个状态集合s(i)（未处理的状态集）

        # 针对字母表中的每个字符c, 这个是啥？ TODO
        for char in string.digits + string.ascii_letters + "".join(['+', '-', '*', '/', '(', ')', '<', '>', '=', '!']):
            # if char == "+":
            #     print("debug")

            s_m = move(state, char)
            s_j = closure(s_m)

            if len(s_j) == 0:  # state 输入char，没有可以匹配的路径
                continue

            next_machine_state = DFAState.new(s_j)

            if DFAState.is_in_state_list(next_machine_state) is False:
                DFAState.dfa_state_list.append(next_machine_state)
                to_handle_state_list.append(s_j)

            current_state_machine = DFAState.new(state)
            current_state_machine.next[char] = next_machine_state

    return begin_dfa_state


def move(s, char):
    """
    即从集合 s 接收一个字符 i，所能到达的新状态的集合
    :param s:
    :param char:
    :return:
    """
    ret_list = []
    for state in s:
        # if state.value in ["begin", "end"]:
        #     for i in state.next_state_list:
        #         ret = move([i], char)   # 命中 TODO:这儿应该还有些问题
        #         if len(ret) > 0:
        #             ret_list.extend([i])
        #
        # elif state.match(char) is True:
        #     ret_list.extend(state.next_state_list)
        #
        #     if state.value.repeat != 0:
        #         ret_list.append(state)
        for next_state in state.next_state_list:
            if next_state.value == "begin":
                match_state_list = move([next_state], char)
                ret_list.extend(match_state_list)

            if next_state.match(char) is True:
                ret_list.append(next_state)

            if isinstance(state.value, EBNFNode) and state.value.repeat != 0:
                if state.match(char) is True:
                    ret_list.append(state)

    return ret_list


def closure(s):
    """
    ε-closure(s)，即集合 s 的ε闭包。也就是从集合 s 中的每个节点，加上从这个节点出发通过ε转换所能到达的所有状态。
    :param s:
    :return:
    """
    # ret_list = []
    # for state in s:
    #     ret_list.append(state)
    #
    #     if isinstance(state.value, EBNFNode):
    #         if state.value.node_type != NodeType.RANGE:
    #             pass
    #         else:  # 只要是 * +号，就认为是可以达到的状态
    #             # ret_list.append(state)
    #             pass
    #     elif state.value == "begin":  # begin
    #         ret_list.extend(state.next_state_list)
    #     else:
    #         pass
    #
    # return ret_list
    return s


def match_dfa(dfa, user_input):
    """
    :param dfa:
    :param user_input:
    :return:
    """
    index = 0

    current_state = dfa   # 初始状态

    while True:
        current_char = user_input[index]

        if current_char not in current_state.next:  # 没有匹配状态
            return False
        else:
            index += 1
            if index == len(user_input):
                return current_state.next[current_char]  # 返回下一个状态集

            current_state = current_state.next[current_char]


def test_match_dfa():
    tree = prepare_regex()
    nfa = to_nfa(tree)

    dfa = nfa2dfa(nfa)
    # dfa.dump()
    assert match_dfa(dfa, "Aaaaaa11111") is not False
    assert match_dfa(dfa, "int") is not False
    assert match_dfa(dfa, "1111122333") is not False
    assert match_dfa(dfa, "111aaaa") is False
    assert match_dfa(dfa, "+") is False
    assert match_dfa(dfa, "1111+") is False


def test_move():
    tree = prepare_regex()
    nfa = to_nfa(tree)
    # nfa.dump()
    x = closure([nfa])
    assert len(x) == 1

    x = move([nfa], "i")
    assert len(x) == 2

    x = move([nfa], "n")
    assert len(x) == 1

    x = move([nfa], "0")
    assert len(x) == 1

    x = move([nfa.next_state_list[0]], "i")   # int   i
    assert len(x) == 1

    x = move([nfa.next_state_list[0]], "z")  # int   i
    assert len(x) == 0

    x = move([nfa.next_state_list[0].next_state_list[0]], "n")   # int
    assert len(x) == 1


def test_parse_1():
    x = parse_1("[a-zA-Z0-9]")
    assert len(x) == len(string.digits + string.ascii_letters)


def test_match_nfa():
    # 对应正则：int|[a-zA-Z][A-Za-Z0-9]*|[0-9]+
    tree = prepare_regex()
    nfa = to_nfa(tree)
    # nfa.dump()
    print(match_nfa(nfa, "int") is True)
    print(match_nfa(nfa, "inA") is True)
    print(match_nfa(nfa, "23") is True)
    print(match_nfa(nfa, "0A") is False)
    print(match_nfa(nfa, "A11112222") is True)

    # 对应正则：a[a-zA-Z0-9]*bc
    tree = prepare_regex_3()
    nfa = to_nfa(tree)
    # nfa.dump()
    print(match_nfa(nfa, "axbc") is True)
    print(match_nfa(nfa, "abcbbbcbc") is True)
    print(match_nfa(nfa, "ab") is False)
    print(match_nfa(nfa, "ddd111bc") is False)
    print(match_nfa(nfa, "a!bc") is False)
    print(match_nfa(nfa, "abaxbc") is True)


if __name__ == "__main__":
    # test_match_nfa()
    # test_move()
    # test_parse_1()
    test_match_dfa()
