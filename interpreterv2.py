from intbase import ErrorType, InterpreterBase
from brewparse import parse_program


class Interpreter(InterpreterBase):
    def __init__(self, console_output=True, inp=None, trace_output=False):
        super().__init__(console_output, inp)  
        self.trace_output = 0  #for debugging purposes
        
    def run(self, program):
        ast = parse_program(program)  #program node (root)
        
        self.variable_name_to_value = {}  # dict to hold variables
        self.variable_name = []    #list of variable names
        
        main_func_node = ast.get("functions")[0]
        if main_func_node.get("name") != "main":
            super().error(ErrorType.NAME_ERROR,"No main() function was found",)
        else:
            self.run_func(main_func_node)
        
        if self.trace_output:
            print("program finished")
            # print(ast.elem_type)
            # print(main_func_node)


           
	
    def run_func(self, function_node):
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
            self.if_statement(statement_node)
            
        elif statement_node.elem_type == "for":   #for loop
            self.for_loop(statement_node)
    
    def do_defination(self, statement_node):
        var_name = statement_node.get("name")
        if var_name in self.variable_name:
            super().error(ErrorType.NAME_ERROR, f"Variable {var_name} defined more than once",)
            return
        self.variable_name.append(var_name)
        self.variable_name_to_value[var_name] = ""   #initial value for any var
        if self.trace_output:
            print("defined variable", var_name)
            
    def find_type(self, op):
        #the input op can be a expression, var
        # print(op)       
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
        else:
            return type
        return type
    
    def match_type(self, t1, t2):   # see if two types match for comparison
        if {t1,t2} in [{"int", "+"}, {"int", "-"}, {"int", "neg"}, {"int", "*"}, {"int", "/"}, {"+", "-"}, {"+", "neg"}, {"+", "*"}, {"+", "/"}, {"-", "neg"}, {"-", "*"}, {"-", "/"}, {"neg", "*"}, {"neg", "/"}, {"*", "/"}]:
            return True
        return t1 == t2

        
    
    def do_assignment(self, statement_node):
        target_var_name = statement_node.get("name")
        
        if not target_var_name in self.variable_name:
            super().error(ErrorType.NAME_ERROR,f"Variable {target_var_name} has not been defined",)
            if self.trace_output:
                print("Undefined variable", target_var_name)
                
        expression_node = statement_node.get("expression")
        resulting_value = self.eval_expression(expression_node)
        self.variable_name_to_value[target_var_name] = resulting_value  #successfully assigned
        if self.trace_output:
                print(target_var_name, "assigned", resulting_value)
    
    def eval_expression(self, expression_node):
        
        if expression_node.elem_type == "var":  #get and its value if it is a variable
            var_name = expression_node.get("name")
            if not var_name in self.variable_name:
                super().error(ErrorType.NAME_ERROR,f"Variable {var_name} has not been defined",)
            return self.variable_name_to_value[var_name]
        
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
            return self.call_function(expression_node)
        
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
        parameters = statement_node.get("args")   #each is an expression
        func_name = statement_node.get("name")
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
            return int(user_input)
        else:  #invalid function call
            super().error(ErrorType.NAME_ERROR,f"Function {func_name} has not been defined",)
    
    
    def if_statement(self, statement_node):   #if branching
        condition = self.eval_expression(statement_node.get("condition"))  #expression, variable or value
        true_statements = statement_node.get("statements")
        false_statements = statement_node.get("else_statements")

        if not isinstance(condition, bool): #only bool condition is allowed
            super().error(ErrorType.TYPE_ERROR,"Incompatible types for if statement condition: "+str(condition))
        if condition:
            for s in true_statements:
                self.run_statement(s)
        else:
            if false_statements:   #if there is a else statement
                for s in false_statements:
                    self.run_statement(s)
        # possible scoping
    
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
                self.run_statement(s)
            self.run_statement(update)
            flag = self.eval_expression(statement_node.get("condition"))
        
        # scoping
        
  


# test cases
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
    program = """func main() {
        var a;
        a = true; print(a);
    print( 1==1 || true || ! (3<5));
    print(! (3<5));
    print("11"+"22"); 
    print( nil == "2");
    print(0 == "0")         ;
    print(nil) ;
    print("true" == "true ")  ;
    print(false != true) ;
            }"""

program = """func main() {
var x;
for (x = 10; x > (1-1); x = x - 1) {  
  var q;
  for (q = 0; q < x; q = q + 1) {
    print(q*q);
  }
}
          }"""


interpreter = Interpreter()
interpreter.run(program)   