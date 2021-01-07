# coding:utf-8
""" NFA实现正则表达式 """
import copy


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

        self.value = value   # 只有三个值：EBNFNode、State("begin")、State("end")
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
        else:  # 匹配上了 或者 可以忘后走时
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
    pass


if __name__ == "__main__":
    # int|[a-zA-Z][A-Za-Z0-9]*|[0-9]+
    tree = prepare_regex()
    nfa = to_nfa(tree)
    nfa.dump()
    print(match_nfa(nfa, "int") is True)
    print(match_nfa(nfa, "inA") is True)
    print(match_nfa(nfa, "23") is True)
    print(match_nfa(nfa, "0A") is False)

    # a[a-zA-Z0-9]*bc
    tree = prepare_regex_3()
    nfa = to_nfa(tree)
    # nfa.dump()
    print(match_nfa(nfa, "axbc") is True)
    print(match_nfa(nfa, "abcbbbcbc") is True)
    print(match_nfa(nfa, "ab") is False)
    print(match_nfa(nfa, "ddd111bc") is False)
    print(match_nfa(nfa, "a!bc") is False)
    print(match_nfa(nfa, "abaxbc") is True)
