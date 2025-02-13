from pyser import Parser, Lexer, Interpreter, TokenType

# Initialize our dynamic components.
lexer = Lexer()
parser = Parser()
interpreter = Interpreter()
tokentype = TokenType()

# Define tokens.
tokentype.add_token("PLUS", '+')
tokentype.add_token("MINUS", '-')
tokentype.add_token("MULTIPLY", '*')
tokentype.add_token("DIVIDE", '/')
tokentype.add_token("LPAREN", '(')
tokentype.add_token("RPAREN", ')')
tokentype.add_auto_token("NUMBER")
tokentype.add_auto_token("STRING")
tokentype.add_token("PRINT", 'print')
# tokentype.add_auto_token("IDENTIFIER")

lexer.add_tokens([
    tokentype["PLUS"],
    tokentype["MINUS"],
    tokentype["MULTIPLY"],
    tokentype["DIVIDE"],
    tokentype["LPAREN"],
    tokentype["RPAREN"],
    tokentype["NUMBER"],
    tokentype["STRING"],
    tokentype["PRINT"]
])

# Define parsing rules dynamically.
parser.new_parsing_rule("paren_math")
parser.new_parsing_rule("math")
parser.new_parsing_rule("math_continuer")
parser.new_parsing_rule("print")
parser["math"] = {
    "a": [tokentype["NUMBER"], tokentype["STRING"]],
    "b": [tokentype["PLUS"],
          tokentype["MINUS"],
          tokentype["MULTIPLY"],
          tokentype["DIVIDE"]],
    "c": [tokentype["NUMBER"], tokentype["STRING"]],
    "optional": [
        parser["math_continuer"]
    ]
}

parser["math_continuer"] = {
    "a": [tokentype["PLUS"],
          tokentype["MINUS"],
          tokentype["MULTIPLY"],
          tokentype["DIVIDE"]],
    "b": [tokentype["NUMBER"], tokentype["STRING"], parser["paren_math"]],
    "optional": [
        parser["math_continuer"]
    ]
}

parser["paren_math"] = {
    "a": [tokentype["LPAREN"]],
    "b": [parser["math"], parser["paren_math"], parser["math_continuer"]],
    "c": [tokentype["RPAREN"]],
    "optional": [
        parser["math_continuer"]
    ]
}

parser["print"] = {
    "a": [tokentype["PRINT"]],
    "b": [tokentype["LPAREN"]],
    "c": [tokentype["STRING"], parser["math"], parser["paren_math"], parser["math_continuer"]],
    "d": [tokentype["RPAREN"]],
}

parser.add_parsing_rules([
    parser["math"],
    parser["math_continuer"],
    parser["paren_math"],
    parser["print"]
])

interpreter.add_interpreting_rule("math")
interpreter.add_interpreting_rule("math_continuer")
interpreter.add_interpreting_rule("paren_math")
interpreter.add_interpreting_rule("print")

# Define interpreting rules.
interpreter.add_interpreting_rules([
    interpreter["math"].parser(parser["math"]),
    interpreter["math_continuer"].parser(parser["math_continuer"]),
    interpreter["paren_math"].parser(parser["paren_math"]),
    interpreter["print"].parser(parser["print"])
])

interpreter.implement_interpreting_rule(interpreter["math"], code="""
if b['type'] == 'PLUS':
    result = float(a['value']) + float(c['value'])
elif b['type'] == 'MINUS':
    result = float(a['value']) - float(c['value'])
elif b['type'] == 'MULTIPLY':
    result = float(a['value']) * float(c['value'])
elif b['type'] == 'DIVIDE':
    result = float(a['value']) / float(c['value'])
stack.append(result)
if optional:
    return interpreter.interpret(optional, stack)
return result
""")

interpreter.implement_interpreting_rule(interpreter["math_continuer"], code="""
if a['type'] == 'PLUS':
    if b['type'] == 'NUMBER':
        result = stack.pop() + float(b['value'])
    else:
        result = stack.pop() + interpreter.interpret(b, stack)
elif a['type'] == 'MINUS':
    if b['type'] == 'NUMBER':
        result = stack.pop() - float(b['value'])
    else:
        result = stack.pop() - interpreter.interpret(b, stack)
elif a['type'] == 'MULTIPLY':
    if b['type'] == 'NUMBER':
        result = stack.pop() * float(b['value'])
    else:
        result = stack.pop() * interpreter.interpret(b, stack)
elif a['type'] == 'DIVIDE':
    if b['type'] == 'NUMBER':
        result = stack.pop() / float(b['value'])
    else:
        result = stack.pop() / interpreter.interpret(b, stack)
stack.append(result)
if optional:
    return interpreter.interpret(optional, stack)
return result
""")

interpreter.implement_interpreting_rule(interpreter["paren_math"], code="""
result = interpreter.interpret(b, stack)
stack.append(result)
if optional:
    return interpreter.interpret(optional, stack)
return result
""")

interpreter.implement_interpreting_rule(interpreter["print"], code="""
if c['type'] == 'STRING':
    print(c['value'])
else:
    print(interpreter.interpret(c))
""")

print("Parser rule:", parser["math"].type)
# Access sub-part "a" from the "math" rule and print its type (should be from the token)
print("Sub-rule a:", parser["math"].a[0].name if isinstance(parser["math"].a, list) else getattr(parser["math"].a, "name", None))

# Make sure the interpreter knows about our lexer and parser.
interpreter.set_lexer(lexer)
interpreter.set_parser(parser)

def evaluate(expression):
    """
    Evaluate a given expression using the interpreter and return its result.
    """
    return interpreter.interpret(expression)

if __name__ == '__main__':
    while True:
        text = input('pyser > ')
        if text == "exit":
            break
        try:
            evaluate(text)
        except Exception as e:
            print("Error:", e)