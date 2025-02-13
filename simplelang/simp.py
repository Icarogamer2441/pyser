from pyser import Lexer, Parser, Interpreter, TokenType

lexer = Lexer()
parser = Parser()
interpreter = Interpreter()
variables = {}

token_type = TokenType()

token_type.add_token("PRINT", "printn")
token_type.add_token("EXECUTE_FILE", "execute_file")
token_type.add_token("LPAREN", "(")
token_type.add_token("RPAREN", ")")
token_type.add_token("SEMICOLON", ";")
token_type.add_auto_token("STRING")
token_type.add_token("ASSIGN", "=")
token_type.add_auto_token("NUMBER")
token_type.add_token("LET", "let")
token_type.add_auto_token("IDENTIFIER")

lexer.add_tokens([
    token_type["PRINT"],
    token_type["LPAREN"],
    token_type["RPAREN"],
    token_type["SEMICOLON"],
    token_type["STRING"],
    token_type["EXECUTE_FILE"],
    token_type["ASSIGN"],
    token_type["NUMBER"],
    token_type["IDENTIFIER"],
    token_type["LET"],
])

parser.new_parsing_rule("program")
parser.new_parsing_rule("statements")
parser.new_parsing_rule("statement")
parser.new_parsing_rule("print_statement")
parser.new_parsing_rule("execute_file")
parser.new_parsing_rule("assignment")
parser.new_parsing_rule("expression")

parser["program"] = {
    "a": [parser["statements"]]
}

parser["statements"] = {
    "a": [parser["statement"]],
    "optional": [parser["statements"]]
}

parser["statement"] = {
    "a": [parser["print_statement"], parser["execute_file"], parser["assignment"]],
    "b": [token_type["SEMICOLON"]]
}

parser["print_statement"] = {
    "a": [token_type["PRINT"]],
    "b": [token_type["LPAREN"]],
    "c": [token_type["STRING"], token_type["IDENTIFIER"]],
    "d": [token_type["RPAREN"]]
}

parser["execute_file"] = {
    "a": [token_type["EXECUTE_FILE"]],
    "b": [token_type["LPAREN"]],
    "c": [token_type["STRING"], token_type["IDENTIFIER"]],
    "d": [token_type["RPAREN"]]
}

parser["assignment"] = {
    "a": [token_type["LET"]],
    "b": [token_type["IDENTIFIER"]],
    "c": [token_type["ASSIGN"]],
    "d": [parser["expression"]]
}

parser["expression"] = {
    "a": [token_type["NUMBER"], token_type["STRING"], token_type["IDENTIFIER"]]
}

parser.add_parsing_rules([
    parser["program"],
    parser["statements"],
    parser["statement"],
    parser["print_statement"],
    parser["execute_file"],
    parser["assignment"],
    parser["expression"]
])

interpreter.add_interpreting_rule("program")
interpreter.add_interpreting_rule("statements")
interpreter.add_interpreting_rule("statement")
interpreter.add_interpreting_rule("print_statement")
interpreter.add_interpreting_rule("execute_file")
interpreter.add_interpreting_rule("assignment")
interpreter.add_interpreting_rule("expression")
interpreter.add_interpreting_rules([
    interpreter["program"].parser(parser["program"]),
    interpreter["statements"].parser(parser["statements"]),
    interpreter["statement"].parser(parser["statement"]),
    interpreter["print_statement"].parser(parser["print_statement"]),
    interpreter["execute_file"].parser(parser["execute_file"]),
    interpreter["assignment"].parser(parser["assignment"]),
    interpreter["expression"].parser(parser["expression"])
])

interpreter.implement_interpreting_rule(interpreter["program"], code="""
return interpreter.interpret(a, stack)
""")

interpreter.implement_interpreting_rule(interpreter["statements"], code="""
result = None
result = interpreter.interpret(a, stack)
if optional:
    result = interpreter.interpret(optional, stack)
return result
""")

interpreter.implement_interpreting_rule(interpreter["statement"], code="""
return interpreter.interpret(a, stack)
""")

interpreter.implement_interpreting_rule(interpreter["print_statement"], code="""
if c['value'] in variables:
    print(variables[c['value']])
else:
    print(c['value'])
return None
""", external_variables=["variables"])

interpreter.implement_interpreting_rule(interpreter["execute_file"], code="""
if c['value'] in variables:
    with open(variables[c['value']].replace('"', ''), 'r') as file:
        interpreter.interpret(file.read(), stack)
else:
    with open(c['value'].replace('"', ''), 'r') as file:
        interpreter.interpret(file.read(), stack)
return None
""", external_variables=["variables"])

interpreter.implement_interpreting_rule(interpreter["assignment"], code="""
variables[b['value']] = interpreter.interpret(d, stack)
return None
""", external_variables=["variables"])

interpreter.implement_interpreting_rule(interpreter["expression"], code="""
if a['type'] == "NUMBER":
    return a['value']
elif a['type'] == "STRING":
    return a['value']
elif a['type'] == "IDENTIFIER":
    return variables[a['value']]
""", external_variables=["variables"])

interpreter.set_lexer(lexer)
interpreter.set_parser(parser)

# Set external context so that dynamic rules can access external variables
interpreter.external_context = {"variables": variables}

while True:
    text = input("> ")
    if text == "exit":
        break
    try:
        interpreter.interpret(text)
    except Exception as e:
        print(e)