#!/usr/bin/env python3
"""Test suite for the safe calculate function"""

import sys
import os
import pytest
import asyncio

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'examples'))

from simple_demo import calculate


class TestCalculateSafety:
    """Test the safe calculate function"""
    
    @pytest.mark.asyncio
    async def test_basic_addition(self):
        result = await calculate("2 + 2")
        assert result["result"] == 4.0
        assert result["expression"] == "2 + 2"
    
    @pytest.mark.asyncio
    async def test_basic_subtraction(self):
        result = await calculate("10 - 3")
        assert result["result"] == 7.0
        
    @pytest.mark.asyncio
    async def test_basic_multiplication(self):
        result = await calculate("5 * 6")
        assert result["result"] == 30.0
        
    @pytest.mark.asyncio
    async def test_basic_division(self):
        result = await calculate("15 / 3")
        assert result["result"] == 5.0
        
    @pytest.mark.asyncio
    async def test_decimal_numbers(self):
        result = await calculate("3.5 + 2.5")
        assert result["result"] == 6.0
        
    @pytest.mark.asyncio
    async def test_parentheses(self):
        result = await calculate("(2 + 3) * 4")
        assert result["result"] == 20.0
        
    @pytest.mark.asyncio
    async def test_nested_parentheses(self):
        result = await calculate("((2 + 3) * 4) / 2")
        assert result["result"] == 10.0
        
    @pytest.mark.asyncio
    async def test_order_of_operations(self):
        result = await calculate("2 + 3 * 4")
        assert result["result"] == 14.0  # Should be 14, not 20
        
    @pytest.mark.asyncio
    async def test_complex_expression(self):
        result = await calculate("(10 + 5) * 2 - 8 / 4")
        assert result["result"] == 28.0  # (15 * 2) - 2 = 30 - 2 = 28
        
    @pytest.mark.asyncio
    async def test_division_by_zero(self):
        result = await calculate("10 / 0")
        assert "error" in result
        assert "Division by zero" in result["error"]
        
    @pytest.mark.asyncio
    async def test_invalid_characters(self):
        result = await calculate("2 + x")
        assert "error" in result
        assert "Invalid characters" in result["error"]
        
    @pytest.mark.asyncio
    async def test_sql_injection_attempt(self):
        result = await calculate("1; DROP TABLE users")
        assert "error" in result
        assert "Invalid characters" in result["error"]
        
    @pytest.mark.asyncio
    async def test_code_injection_attempt(self):
        result = await calculate("__import__('os').system('ls')")
        assert "error" in result
        assert "Invalid characters" in result["error"]
        
    @pytest.mark.asyncio
    async def test_unbalanced_parentheses(self):
        result = await calculate("(2 + 3")
        assert "error" in result
        assert "Unbalanced parentheses" in result["error"]
        
    @pytest.mark.asyncio
    async def test_negative_numbers(self):
        result = await calculate("-5 + 3")
        assert result["result"] == -2.0
        
    @pytest.mark.asyncio
    async def test_double_negative(self):
        result = await calculate("5 - -3")
        assert result["result"] == 8.0
        
    @pytest.mark.asyncio
    async def test_whitespace_handling(self):
        result = await calculate("  2   +   3  ")
        assert result["result"] == 5.0
        
    @pytest.mark.asyncio
    async def test_large_numbers(self):
        result = await calculate("1000000 * 2")
        assert result["result"] == 2000000.0
        
    @pytest.mark.asyncio
    async def test_float_precision(self):
        result = await calculate("0.1 + 0.2")
        # Due to float precision, we check if it's close enough
        assert abs(result["result"] - 0.3) < 0.0001


if __name__ == "__main__":
    pytest.main([__file__, "-v"])