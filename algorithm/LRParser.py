# coding:utf-8
"""
规约算法判断字符串是否计算公式的子串
https://gist.github.com/zTrix/3d3266673d3ff84a302d

1. 计算follow
2. 尝试规约
3. 尝试移进
"""

rules = {
    'E': ['A'],
    'A': ['A+M', 'M'],
    'M': ['M*P', 'P'],
    'P': ['(E)', 'N'],
    'N': [str(i) for i in range(10)],
}


def reduce(s):

    if s == "E":
        return True

    for i in range(0, len(s)):
        for j in range(i, len(s)):
            sub = s[i:j+1]

            for r in rules:
                for rr in rules[r]:
                    if sub == rr:
                        if j + 1 == len(s):
                            new_s = s[:i] + r
                        else:
                            new_s = s[:i] + r + s[j+1:]

                        print("(%s,%s)\t %s -> %s\t%s" % (i, j, sub, r, s))
                        if reduce(new_s):
                            return True
    return False


def reduce1(s):

    if s == "E":
        return True

    i = 0
    for j in range(i, len(s)):
        sub = s[i:j+1]

        for r in rules:
            for rr in rules[r]:
                if sub == rr:
                    if j + 1 == len(s):
                        new_s = s[:i] + r
                    else:
                        new_s = s[:i] + r + s[j+1:]

                    print("(%s,%s)\t %s -> %s\t%s" % (i, j, sub, r, s))
                    if reduce(new_s):
                        return True
    return False


if __name__ == "__main__":
    print(reduce1("A+M"))
