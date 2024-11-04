from intbase import ErrorType, InterpreterBase
from brewparse import parse_program


class Interpreter(InterpreterBase):
    def __init__(self, console_output=True, inp=None, trace_output=False):
        super().__init__(console_output, inp)  
        self.trace_output = 0  #for debugging purposes
        
    def run(self, program):
        ast = parse_program(program)  #program node (root)
        
        var_name_to_value = {}  # dict to hold variables
        self.functions = {} # hold defined functions
        self.scope_stack = [var_name_to_value]   #scope stack to save scopes
        main_node = 0
        self.function_output = None #saving rerturn values
        for function_node in ast.get("functions"):
            
            if function_node.get("name") == "main":
                main_node = function_node
                continue
            else:  #define functions
                name =  function_node.get("name")
                args =  function_node.get("args")
                statements = function_node.get("statements")
                func_key = name + str(len(args))   # foo(a) = "foo1"  foo(a,b) = "foo2"
                self.functions[func_key] = [args,statements]
        # print(self.functions)
        if main_node:
            self.run_main(main_node)
        else:
            super().error(ErrorType.NAME_ERROR,"No main() function was found",)
        if self.trace_output:
            print("program finished")
            # print(ast.elem_type)
            # print(main_func_node)




            
            
    def run_main(self, function_node):  #running the main function
        
        for statement in function_node.get("statements"):
            self.run_statement(statement)
    
    def run_statement(self, statement_node):
        if statement_node.elem_type == "vardef":   #variable defination
            self.do_defination(statement_node)
        
        elif statement_node.elem_type == "=":   #variable assignment
            self.do_assignment(statement_node)

        elif statement_node.elem_type == "fcall":   #function call
            self.call_function(statement_node)
        
        elif statement_node.elem_type == "if":   #if statements
            return self.if_statement(statement_node)
            
        elif statement_node.elem_type == "for":   #for loop
            return self.for_loop(statement_node)
        
        elif statement_node.elem_type == "return":   #for loop
            self.return_from(statement_node)
            if self.trace_output:
                print("returned")
            # stack pop to boundtry (none)
            while self.scope_stack:
                popped_element = self.scope_stack.pop()
            
                if popped_element is None:
                    # print("Encountered None, stopping.")
                    break
            return "returned"
        return "continue"

    
    def do_defination(self, statement_node):   #define variable in the local scope
        var_name = statement_node.get("name")
        
        stack = self.scope_stack
        scope = stack[-1]    #current scope
        if var_name in scope:
            super().error(ErrorType.NAME_ERROR, f"Variable {var_name} defined more than once",)
            return
        scope[var_name] = ""   #initial value for any var
        if self.trace_output:
            print("defined variable", var_name)        
    
    def do_assignment(self, statement_node):    #assign variable in the current scopes
        target_var_name = statement_node.get("name")
        expression_node = statement_node.get("expression")
        resulting_value = self.eval_expression(expression_node)
        
        stack = self.scope_stack
        for scope in reversed(stack):   
            if scope is None: # Stop at the function boundary marker
                break
            if target_var_name in scope:
                scope[target_var_name] = resulting_value
                return
        super().error(ErrorType.NAME_ERROR,f"Variable {target_var_name} has not been defined",)

        if self.trace_output:
                print(target_var_name, "assigned", resulting_value)

        
    def find_type(self, op):
        #the input op can be a expression, var   
        type = op.elem_type     #when it is a expression or variable
        if type == "var":    
            if isinstance(self.eval_expression(op), str):
                type = "string"
            if isinstance(self.eval_expression(op), int):
                type = "int"
            if isinstance(self.eval_expression(op), bool):
                type = "bool"
            if self.eval_expression(op) is None:
                type = "nil"   
        elif type == "fcall":
            type = "ok"
            # self.eval_expression(op)
            # if isinstance(self.function_output, str):
            #     type = "string"
            # if isinstance(self.function_output, int):
            #     type = "int"
            # if isinstance(self.function_output, bool):
            #     type = "bool"
            # if self.function_output is None:
            #     type = "nil"   
        else:
            return type
        return type
    
    def match_type(self, t1, t2):   # see if two types match for comparison
        allowed = [
            {"int", "+"}, {"int", "-"}, {"int", "neg"}, {"int", "*"}, {"int", "/"}, 
            {"+", "-"}, {"+", "neg"}, {"+", "*"}, {"+", "/"}, {"-", "neg"}, 
            {"-", "*"}, {"-", "/"}, {"neg", "*"}, {"neg", "/"}, {"*", "/"}
        ]
        if t1 == "ok" or t2 == "ok" or {t1,t2} in allowed:
            return True
        return t1 == t2
    
    def eval_expression(self, expression_node):
        try:
            expression_node.elem_type
        except:
            return expression_node
        if expression_node.elem_type == "var":  #get and its value if it is a variable
            var_name = expression_node.get("name")
            
            for scope in reversed(self.scope_stack): #get the variable value in the current scopes
                if scope is None:  # Stop at the function boundary marker
                    break
                if var_name in scope:
                    return scope[var_name]
            super().error(ErrorType.NAME_ERROR,f"Variable {var_name} has not been defined",)

            # if not var_name in self.variable_name_to_value.keys():
            #     super().error(ErrorType.NAME_ERROR,f"Variable {var_name} has not been defined",)
            # return self.variable_name_to_value[var_name]
        
        elif expression_node.elem_type in ["int", "string","bool"]:  #return if it is a value
            return expression_node.get("val")
        elif expression_node.elem_type == "nil":
            return None
        elif expression_node.elem_type in ["+","-", "*","/"]:   #calculate if it is arithmetic binary op
            op1 = expression_node.get("op1")
            op2 = expression_node.get("op2")
            type1 = self.find_type(op1)
            type2 = self.find_type(op2)
            # if string + string: ok to concatenate
            # otherwise non-int not allowed [nil, bool, string]
    
            if self.trace_output:   
                print("calculating",type1, type2, expression_node.elem_type)
            
            if expression_node.elem_type ==  "+": #concatenation valid cases and invalid cases
                if isinstance(self.eval_expression(op1), str) and isinstance(self.eval_expression(op2), str):
                    return self.eval_expression(op1) + self.eval_expression(op2)
                if isinstance(self.eval_expression(op1), str) and isinstance(self.eval_expression(op2), int):
                    super().error(ErrorType.TYPE_ERROR,"Incompatible types for arithmetic operation:"+type1+" "+type2,)
                if isinstance(self.eval_expression(op2), str) and isinstance(self.eval_expression(op1), int):
                    super().error(ErrorType.TYPE_ERROR,"Incompatible types for arithmetic operation:"+type1+" "+type2,)
            
            
            if type1 in ["string", "bool", "nil"] or type2 in ["string", "bool", "nil"]:
                super().error(ErrorType.TYPE_ERROR,"Incompatible types for arithmetic operation: "+type1+" "+type2,)
                return
            if expression_node.elem_type ==  "+":
                return self.eval_expression(op1) + self.eval_expression(op2)
            if expression_node.elem_type ==  "-":
                return self.eval_expression(op1) - self.eval_expression(op2)
            if expression_node.elem_type ==  "*":
                return self.eval_expression(op1) * self.eval_expression(op2)
            if expression_node.elem_type ==  "/":
                return self.eval_expression(op1) // self.eval_expression(op2)
            
        elif expression_node.elem_type == "fcall":  #function call only case is inputi()
            self.call_function(expression_node)
            return self.function_output
        
        elif expression_node.elem_type == "neg":  # unary negation
            op1 = expression_node.get("op1")
            type1 = self.find_type(op1)
            if not type1 == "int":  #only for int
                super().error(ErrorType.TYPE_ERROR,"Incompatible types for int negation: "+type1)
            return -1*self.eval_expression(op1)
        
        elif expression_node.elem_type == "!":  # logical negation
            op1 = expression_node.get("op1")
            type1 = self.find_type(op1)
            allowed_types = ["bool",'==', '<', '<=', '>', '>=', '!=',"||","&&","!"]
            if not type1 in allowed_types:  #only for int
                super().error(ErrorType.TYPE_ERROR,"Incompatible types for logical negation: "+type1)
            return not self.eval_expression(op1)
        
        elif expression_node.elem_type in ['||', '&&']:   #logical operation
            op1 = expression_node.get("op1")     #get the type of left and right
            op2 = expression_node.get("op2")
            type1 = self.find_type(op1)
            type2 = self.find_type(op2)
            
            allowed_types = ["bool",'==', '<', '<=', '>', '>=', '!=',"||","&&","!"]
            if not type1 in allowed_types or not type2 in allowed_types:
                super().error(ErrorType.TYPE_ERROR,"Incompatible types for logical operation: "+type1+" "+type2,)
            if expression_node.elem_type ==  "||":
                return (lambda: self.eval_expression(op1))() or (lambda: self.eval_expression(op2))() #strict evaluation
            if expression_node.elem_type ==  "&&":
                return (lambda: self.eval_expression(op1))() and (lambda: self.eval_expression(op2))() #strict evaluation

        elif expression_node.elem_type in ['==', '<', '<=', '>', '>=', '!=']:   #compare operations
            op1 = expression_node.get("op1")     #get the type of left and right
            op2 = expression_node.get("op2")
            type1 = self.find_type(op1)
            type2 = self.find_type(op2)
            if self.trace_output:
                print("comparing",type1, type2, expression_node.elem_type)
            
            if not self.match_type(type1,type2):     #if two types dont match
                if expression_node.elem_type == '==':
                    return False
                elif expression_node.elem_type == '!=':
                    return True
                else:
                    super().error(ErrorType.TYPE_ERROR,"Incompatible types for comparison operation: "+type1+" "+type2,)
            
            #if the types do match
            if expression_node.elem_type == '==':
                return self.eval_expression(op1) == self.eval_expression(op2)
            if expression_node.elem_type == '<':
                return self.eval_expression(op1) < self.eval_expression(op2)
            if expression_node.elem_type == '>':
                return self.eval_expression(op1) > self.eval_expression(op2)
            if expression_node.elem_type == '<=':
                return self.eval_expression(op1) <= self.eval_expression(op2)
            if expression_node.elem_type == '>=':
                return self.eval_expression(op1) >= self.eval_expression(op2)
            if expression_node.elem_type == '!=':
                return not self.eval_expression(op1) == self.eval_expression(op2)
            

    def call_function(self, statement_node):
        parameters = statement_node.get("args")   #list of parameters, each is an expressions
        func_name = statement_node.get("name")
        func_key = func_name + str(len(parameters))
        # print(func_key)
        if self.trace_output:
            print(f"tried to call {func_name}")
            
        if func_name == "print":
            output = ""
            for i in parameters:
                parts = self.eval_expression(i)
                if str(parts) == "True":  #fix True to be true
                    parts = "true"
                if str(parts) == "False":
                    parts = "false"
                output += str(parts)
            super().output(output)
            if self.trace_output:
                print("printed: "+output)
                
        elif func_name == "inputi":
            if len(parameters) == 1:
                super().output(parameters[0].get("val"))
            elif len(parameters) > 1:
                super().error(ErrorType.NAME_ERROR,f"No inputi() function found that takes > 1 parameter",)
            user_input = super().get_input()
            self.function_output = int(user_input)
            return int(user_input)
        
        elif func_key in self.functions:   #a self defined function
            if self.trace_output:
                print(func_key,"is called with",parameters)
            args = self.functions[func_key][0]   #list of arguments
            statements = self.functions[func_key][1]
            
            # start to scope
            self.scope_stack.append(None)   #set a function boundry marker
            func_scope = {}
            self.scope_stack.append(func_scope)  #scope is ready
            for i in range(len(args)):   #define and set the arguments
                self.do_defination(args[i])
                self.do_assignment(  { "name": args[i].get("name"), "expression":parameters[i]} )
            
            for statement in statements:
                result = self.run_statement(statement)
                
                if not result == "continue":
                    if self.trace_output:
                        print("return from",func_key)

                    return self.function_output
            #remove the scope
            self.scope_stack.pop()
            self.scope_stack.pop()
            return self.function_output  #default return
                
            
        else:  #invalid function call
            super().error(ErrorType.NAME_ERROR,f"Function {func_name} has not been defined",)
    
    
    def if_statement(self, statement_node):   #if branching
        condition = self.eval_expression(statement_node.get("condition"))  #expression, variable or value
        true_statements = statement_node.get("statements")
        false_statements = statement_node.get("else_statements")

        if not isinstance(condition, bool): #only bool condition is allowed
            super().error(ErrorType.TYPE_ERROR,"Incompatible types for if statement condition: "+str(condition))
            
        # start to scope
        if_scope = {}
        self.scope_stack.append(if_scope)
        
        if condition:
            for s in true_statements:
                result = self.run_statement(s)
                
                if not result == "continue":
                    return "returned"
        else:
            if false_statements:   #if there is a else statement
                for s in false_statements:
                    result = self.run_statement(s)
                
                    if not result == "continue":
                        return "returned"
                    
        # possible scoping
        self.scope_stack.pop()
    
    def for_loop(self, statement_node):    #for loop
        init = statement_node.get("init")
        self.run_statement(init)
        flag = self.eval_expression(statement_node.get("condition"))
        update = statement_node.get("update")
        statements = statement_node.get("statements")

        if not isinstance(flag, bool): #only bool condition is allowed
            super().error(ErrorType.TYPE_ERROR,"Incompatible types for for loop condition: "+str(flag))

        while(flag):
            for s in statements:
                result = self.run_statement(s)
                
                if not result == "continue":
                    return "returned"
                
            self.run_statement(update)
            flag = self.eval_expression(statement_node.get("condition"))
        
        
    def return_from(self, statement_node):
        expression = statement_node.get("expression")
        self.function_output = self.eval_expression(expression)
        # print("function output is set to",self.function_output)
        # return self.eval_expression(expression)


# test cases
program = 1
if True: 
    program = """
    func main() {
    var a;
    var b;
    var c;
    var d; var foo; var bar; var bletch; var prompt; var boo;
    foo = "5";  
    var _bar_bletch;
    a = foo;
    print(2 + inputi(3));
        bar = 3 - 4;
    print(bar);
        bletch = 3 - (5 + 2);
        prompt = "enter a number: ";

        boo = inputi("Enter a number: ");
    print(boo+89898989);

    }

    """
    program = """
func foo() { 
 print("hello");
 /* no explicit return command */
}

func bar() {
  return 1;  /* no return value specified */
}

func main() {
   var val;
   val = nil;
   print(bar() + 1);
   if (foo() == val && true) { print("this should print!"); }
}

"""



interpreter = Interpreter()
interpreter.run(program)   