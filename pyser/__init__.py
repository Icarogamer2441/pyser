import re

# -----------------
# Token and TokenType
# -----------------
class Token:
    def __init__(self, type_def, value, position):
        self.type = type_def  # a TokenDefinition instance
        self.value = value
        self.position = position  # position in the input text

    def __repr__(self):
        return f"Token({self.type.name}, {self.value})"

class TokenDefinition:
    def __init__(self, name, value=None, pattern=None):
        self.name = name
        self.value = value       # literal value if provided
        self.pattern = pattern   # regex pattern for auto tokens

    def __repr__(self):
        return f"<TokenType {self.name}>"

    def __eq__(self, other):
        if isinstance(other, TokenDefinition):
            return self.name == other.name and self.value == other.value
        return False

class TokenType:
    def __init__(self):
        self.tokens = {}  # map from token names to TokenDefinition objects

    def add_token(self, name, literal):
        # Creates a literal token type.
        self.tokens[name] = TokenDefinition(name, value=literal)
    
    def add_auto_token(self, name):
        # Only add the auto token if it hasn't already been defined
        if name in self.tokens:
            return

        # Creates an auto token, with a regex pattern based on the name.
        if name == "NUMBER":
            pattern = r'\d+(\.\d+)?'
        elif name == "STRING":
            pattern = r'"[^"]*"'
        elif name == "IDENTIFIER":
            pattern = r'[A-Za-z_]\w*'
        else:
            pattern = r'\w+'
        self.tokens[name] = TokenDefinition(name, pattern=pattern)

    def __getitem__(self, key):
        return self.tokens[key]

    def __repr__(self):
        return f"TokenType({self.tokens})"

# -----------------
# Lexer
# -----------------
class Lexer:
    def __init__(self):
        self.token_defs = []  # ordered list of TokenDefinition objects

    def add_tokens(self, token_defs):
        self.token_defs.extend(token_defs)

    def tokenize(self, text):
        tokens = []
        position = 0
        text = text.strip()
        while position < len(text):
            # Skip any whitespace
            ws = re.match(r'\s+', text[position:])
            if ws:
                position += ws.end()
            if position >= len(text):
                break

            match_found = False

            # First, try matching literal tokens (tokens with a fixed value)
            for token_def in self.token_defs:
                if token_def.value is not None:
                    literal = token_def.value
                    if text.startswith(literal, position):
                        tokens.append(Token(token_def, literal, position))
                        position += len(literal)
                        match_found = True
                        break

            # If a literal token was found, continue to the next text portion.
            if match_found:
                continue

            # Then try matching auto tokens (tokens based on a regex pattern)
            for token_def in self.token_defs:
                if token_def.value is None:
                    m = re.match(token_def.pattern, text[position:])
                    if m:
                        value = m.group(0)
                        tokens.append(Token(token_def, value, position))
                        position += len(value)
                        match_found = True
                        break
            if not match_found:
                raise ValueError(f"Unexpected token at position {position}: {text[position:]}")
        return tokens

# -----------------
# Parser
# -----------------
class ParsingRule:
    def __init__(self, name):
        self.name = name
        self.definition = {}  # rule parts definitions

    @property
    def type(self):
        return self.name

    def update_definition(self, definition):
        self.definition = definition
        # Also create attributes (like .a, .b, etc.) to access parts easily
        for key, value in definition.items():
            setattr(self, key, value)

    def __repr__(self):
        return f"<ParsingRule {self.name}>"

class Parser:
    def __init__(self):
        self.rules = {}  # mapping from rule name to ParsingRule instance

    def new_parsing_rule(self, name):
        self.rules[name] = ParsingRule(name)

    def __getitem__(self, key):
        return self.rules[key]

    def __setitem__(self, key, value):
        # Expect value to be a dict with keys like "a", "b", "c", "optional"
        if key in self.rules:
            self.rules[key].update_definition(value)
        else:
            self.rules[key] = ParsingRule(key)
            self.rules[key].update_definition(value)

    def add_parsing_rules(self, rules_list):
        # This method is provided for API symmetry. In this simple impl.
        # the rules are already stored in self.rules.
        pass

    def parse(self, tokens, start_rule_name):
        rule = self.rules[start_rule_name]
        result, pos = self._parse_rule(rule, tokens, 0)
        if result is None or pos != len(tokens):
            raise ValueError("Parsing failed")
        return result

    def _parse_rule(self, rule, tokens, pos):
        # Create a node that represents this rule.
        node = {"type": rule.name}
        start_pos = pos
        # Process all rule parts except "optional" (preserving insertion order).
        for part in [k for k in rule.definition.keys() if k != "optional"]:
            alternatives = rule.definition[part]
            parsed = None
            for alt in alternatives:
                res, new_pos = self._parse_element(alt, tokens, pos)
                if res is not None:
                    parsed = res
                    pos = new_pos
                    break
            if parsed is None:
                return None, start_pos
            node[part] = parsed

        # Process any optional parts if specified.
        if "optional" in rule.definition:
            opt_results = []
            while True:
                parsed_any = False
                for opt in rule.definition["optional"]:
                    res, new_pos = self._parse_element(opt, tokens, pos)
                    if res is not None:
                        opt_results.append(res)
                        pos = new_pos
                        parsed_any = True
                        break
                if not parsed_any:
                    break
            if opt_results:
                node["optional"] = opt_results
        return node, pos

    def _parse_element(self, element, tokens, pos):
        # element can be:
        # - a TokenDefinition: match a single token if its type equals the definition.
        # - a ParsingRule: recursively parse.
        # - a dict: treat it as a rule definition.
        if isinstance(element, TokenDefinition):
            if pos < len(tokens) and tokens[pos].type == element:
                return {"type": tokens[pos].type.name, "value": tokens[pos].value}, pos+1
            else:
                return None, pos
        elif isinstance(element, ParsingRule):
            return self._parse_rule(element, tokens, pos)
        elif isinstance(element, dict):
            temp_rule = ParsingRule("temp")
            temp_rule.update_definition(element)
            return self._parse_rule(temp_rule, tokens, pos)
        else:
            return None, pos

# -----------------
# Interpreter
# -----------------
class InterpretingRule:
    def __init__(self, rule_name):
        self.rule_name = rule_name
        self.code = None  # the code snippet to execute
        self.parser_rule = None

    def parser(self, parser_rule):
        self.parser_rule = parser_rule
        return self

    def __repr__(self):
        return f"<InterpretingRule {self.rule_name}>"

class Interpreter:
    def __init__(self):
        self.rules = {}  # mapping from rule names to InterpretingRule instances
        self.interpreting_rules = []  # list of all interpreting rules
        # We'll hold references to a Lexer and Parser for the full pipeline.
        self.lexer = None
        self.parser = None

    def __getitem__(self, key):
        if key not in self.rules:
            self.rules[key] = InterpretingRule(key)
        return self.rules[key]

    def add_interpreting_rules(self, rules_list):
        self.interpreting_rules.extend(rules_list)

    def implement_interpreting_rule(self, rule, code, external_variables=None):
        rule.code = code
        # Store the list of external variable names (if any) with this rule.
        rule.external_variable_names = external_variables if external_variables is not None else []

    def add_interpreting_rule(self, rule_name):
        """
        Add (or create) an interpreting rule with the given name and add it to the 
        interpreter's list of interpreting_rules.
        Returns the interpreting rule instance.
        """
        rule = self[rule_name]  # __getitem__ creates the rule if it doesn't exist.
        if rule not in self.interpreting_rules:
            self.interpreting_rules.append(rule)
        return rule

    def set_lexer(self, lexer):
        self.lexer = lexer

    def set_parser(self, parser):
        self.parser = parser

    def interpret(self, input_data, stack=None):
        if stack is None:
            stack = []
        # Allow both text input and a precomputed parse tree.
        if isinstance(input_data, str):
            if self.lexer is None or self.parser is None:
                raise ValueError("Lexer and Parser must be set before interpretation")
            tokens = self.lexer.tokenize(input_data)
            # Dynamic start rule selection:
            if "program" in self.parser.rules:
                start_rule = "program"
            else:
                candidate = tokens[0].type.name if tokens else "math"
                # Try an exact match first...
                if candidate in self.parser.rules:
                    start_rule = candidate
                # ...otherwise check for a lowercased match (to allow, e.g., "PRINT" -> "print")
                elif candidate.lower() in self.parser.rules:
                    start_rule = candidate.lower()
                # Special-case for parentheses if defined.
                elif candidate == "LPAREN" and "paren_math" in self.parser.rules:
                    start_rule = "paren_math"
                else:
                    start_rule = "math"
            parse_tree = self.parser.parse(tokens, start_rule)
        elif isinstance(input_data, dict):
            parse_tree = input_data
        elif isinstance(input_data, list):
            if input_data:
                parse_tree = input_data[0]
            else:
                raise ValueError("Empty parse tree list passed for interpretation")
        else:
            raise ValueError("Unsupported input type for interpretation")

        # Prepare local namespace for the dynamic code.
        local_vars = {
            "stack": stack,
            "tokentype": None,  # In this simple implementation, we leave tokentype as None.
            "optional": parse_tree.get("optional"),  # Inject the optional part (if any)
            "interpreter": self                      # Make interpreter available inside dynamic code
        }

        rule_name = parse_tree.get("type")
        if rule_name in self.rules and self.rules[rule_name].code is not None:
            # We try to extract keys 'a', 'b', 'c' from the parse tree.
            a = parse_tree.get("a")
            b = parse_tree.get("b")
            c = parse_tree.get("c")
            d = parse_tree.get("d")
            local_vars.update({"a": a, "b": b, "c": c, "d": d})
            try:
                # Dynamically define an interpreting function and run it.
                exec_globals = {}
                exec("def interpret_rule(a, b, c, stack, tokentype):\n" +
                     "\n".join("    " + line for line in self.rules[rule_name].code.splitlines()),
                     exec_globals)
                # Update exec_globals with additional names so that the code snippet sees them.
                exec_globals.update({
                    "optional": local_vars["optional"],
                    "interpreter": self,
                    "d": local_vars["d"]
                })
                # Inject external variables from the interpreter's external_context if specified by this rule.
                rule_obj = self.rules[rule_name]
                if hasattr(rule_obj, 'external_variable_names'):
                    for var in rule_obj.external_variable_names:
                        if hasattr(self, "external_context") and var in self.external_context:
                            exec_globals[var] = self.external_context[var]
                result = exec_globals["interpret_rule"](a, b, c, stack, local_vars["tokentype"])
                return result
            except Exception as e:
                print("Error during interpretation:", e)
        else:
            print("No interpreting rule implemented for", rule_name)

# Expose the main classes at the package level.
__all__ = ["TokenType", "Lexer", "Parser", "Interpreter", "Token"]
