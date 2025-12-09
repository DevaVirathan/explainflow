"""
Tests for ExplainFlow core module.
"""

import pytest
from explainflow import explain, ExecutionTrace
from explainflow.models import Variable, ExecutionStep, StepType


class TestExplainFunction:
    """Tests for the explain() function."""
    
    def test_simple_assignment(self):
        """Test basic variable assignment."""
        code = "x = 5"
        trace = explain(code, output="silent")
        
        assert isinstance(trace, ExecutionTrace)
        assert trace.success
        assert len(trace.steps) > 0
        assert "x" in trace.final_variables
        assert trace.final_variables["x"].repr_value == "5"
    
    def test_multiple_assignments(self):
        """Test multiple variable assignments."""
        code = """
x = 5
y = 10
z = x + y
"""
        trace = explain(code, output="silent")
        
        assert trace.success
        assert "x" in trace.final_variables
        assert "y" in trace.final_variables
        assert "z" in trace.final_variables
        assert trace.final_variables["z"].repr_value == "15"
    
    def test_print_output(self):
        """Test that print output is captured."""
        code = """
print("Hello, World!")
"""
        trace = explain(code, output="silent")
        
        assert trace.success
        assert "Hello, World!" in trace.final_output
    
    def test_loop_execution(self):
        """Test loop tracing."""
        code = """
total = 0
for i in range(3):
    total += i
"""
        trace = explain(code, output="silent")
        
        assert trace.success
        assert trace.final_variables["total"].repr_value == "3"
        # Should have multiple steps for loop iterations
        assert len(trace.steps) > 3
    
    def test_function_definition_and_call(self):
        """Test function definition and execution."""
        code = """
def add(a, b):
    return a + b

result = add(3, 4)
"""
        trace = explain(code, output="silent")
        
        assert trace.success
        assert "result" in trace.final_variables
        assert trace.final_variables["result"].repr_value == "7"
    
    def test_conditional_execution(self):
        """Test if/else tracing."""
        code = """
x = 10
if x > 5:
    result = "big"
else:
    result = "small"
"""
        trace = explain(code, output="silent")
        
        assert trace.success
        assert trace.final_variables["result"].repr_value == "'big'"
    
    def test_list_operations(self):
        """Test list manipulation tracing."""
        code = """
numbers = [1, 2, 3]
numbers.append(4)
length = len(numbers)
"""
        trace = explain(code, output="silent")
        
        assert trace.success
        assert trace.final_variables["length"].repr_value == "4"
    
    def test_syntax_error(self):
        """Test handling of syntax errors."""
        code = "x = "  # Invalid syntax
        trace = explain(code, output="silent")
        
        assert not trace.success
        assert "SyntaxError" in trace.error_message
    
    def test_runtime_error(self):
        """Test handling of runtime errors."""
        code = """
x = 1 / 0
"""
        trace = explain(code, output="silent")
        
        assert not trace.success
        assert "ZeroDivisionError" in trace.error_message
    
    def test_max_steps_limit(self):
        """Test that max_steps limit is respected."""
        code = """
while True:
    x = 1
"""
        trace = explain(code, output="silent", max_steps=10)
        
        # Should stop due to max_steps, not hang
        assert len(trace.steps) <= 10


class TestVariable:
    """Tests for the Variable class."""
    
    def test_from_value_int(self):
        """Test Variable creation from integer."""
        var = Variable.from_value("x", 42)
        
        assert var.name == "x"
        assert var.value == 42
        assert var.type_name == "int"
        assert var.repr_value == "42"
    
    def test_from_value_string(self):
        """Test Variable creation from string."""
        var = Variable.from_value("name", "hello")
        
        assert var.name == "name"
        assert var.type_name == "str"
        assert var.repr_value == "'hello'"
    
    def test_from_value_list(self):
        """Test Variable creation from list."""
        var = Variable.from_value("items", [1, 2, 3])
        
        assert var.name == "items"
        assert var.type_name == "list"
        assert var.repr_value == "[1, 2, 3]"
    
    def test_changed_detection(self):
        """Test that changed flag is set correctly."""
        var1 = Variable.from_value("x", 5, previous_value=5)
        var2 = Variable.from_value("x", 10, previous_value=5)
        
        assert not var1.changed
        assert var2.changed
    
    def test_long_repr_truncation(self):
        """Test that long repr values are truncated."""
        long_string = "a" * 200
        var = Variable.from_value("long", long_string)
        
        assert len(var.repr_value) <= 103  # 100 + "..."


class TestExecutionTrace:
    """Tests for the ExecutionTrace class."""
    
    def test_len(self):
        """Test __len__ method."""
        trace = ExecutionTrace(code="x = 1")
        trace.steps = [
            ExecutionStep(1, 1, "x = 1", StepType.ASSIGNMENT),
        ]
        
        assert len(trace) == 1
    
    def test_iteration(self):
        """Test iteration over trace."""
        trace = ExecutionTrace(code="x = 1")
        trace.steps = [
            ExecutionStep(1, 1, "x = 1", StepType.ASSIGNMENT),
            ExecutionStep(2, 2, "y = 2", StepType.ASSIGNMENT),
        ]
        
        steps = list(trace)
        assert len(steps) == 2
    
    def test_get_step(self):
        """Test get_step method."""
        trace = ExecutionTrace(code="x = 1")
        step = ExecutionStep(1, 1, "x = 1", StepType.ASSIGNMENT)
        trace.steps = [step]
        
        assert trace.get_step(1) == step
        assert trace.get_step(999) is None
    
    def test_get_lines_executed(self):
        """Test get_lines_executed method."""
        trace = ExecutionTrace(code="x = 1\ny = 2")
        trace.steps = [
            ExecutionStep(1, 1, "x = 1", StepType.ASSIGNMENT),
            ExecutionStep(2, 2, "y = 2", StepType.ASSIGNMENT),
        ]
        
        lines = trace.get_lines_executed()
        assert lines == [1, 2]
    
    def test_summary(self):
        """Test summary method."""
        code = "x = 5"
        trace = explain(code, output="silent")
        
        summary = trace.summary()
        
        assert "Execution Summary" in summary
        assert "Total steps:" in summary
        assert "Success: True" in summary


class TestExecutionStep:
    """Tests for the ExecutionStep class."""
    
    def test_get_variable_summary_empty(self):
        """Test variable summary with no variables."""
        step = ExecutionStep(1, 1, "pass", StepType.LINE)
        
        assert step.get_variable_summary() == "No variables"
    
    def test_get_variable_summary_with_vars(self):
        """Test variable summary with variables."""
        step = ExecutionStep(1, 1, "x = 5", StepType.ASSIGNMENT)
        step.variables = {
            "x": Variable.from_value("x", 5)
        }
        
        summary = step.get_variable_summary()
        assert "x = 5" in summary
