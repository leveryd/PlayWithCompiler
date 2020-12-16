# PlayScript-python3

This repo is a simple calculator implemented with ANTLR4 and Python3.

This project is inspired by [编译原理之美](https://time.geekbang.org/column/intro/219), which is a Course Design of Compiling using ANTLR4.


## 🚚 step1 install

### install antlr4

Follow the instruction on [Antlr4](https://www.antlr.org/). 

```bash
cd /usr/local/lib
sudo curl -O https://www.antlr.org/download/antlr-4.8-complete.jar

export CLASSPATH=".:/usr/local/lib/antlr-4.8-complete.jar:$CLASSPATH"
alias antlr4='java -jar /usr/local/lib/antlr-4.8-complete.jar'
alias grun='java org.antlr.v4.gui.TestRig'
```

### install python runtime

Details can be found in [python-target](https://github.com/antlr/antlr4/blob/master/doc/python-target.md).

```bash
pip3 install antlr4-python3-runtime
```

## 🧱 step2 use `.g4` to generate parser and lexer 

```bash
antlr4 -Dlanguage=Python3 PlayScript.g4 -visitor -o dist 
```
Use `-visitor` to generate Visitor Class
Use `-o` to specify output path.

## 🎉 step3 done

```bash
python3 main.py
```

