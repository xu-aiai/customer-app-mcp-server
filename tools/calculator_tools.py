import logging
import math
import random

logger = logging.getLogger("Calculator")


def calculate_expression(python_expression: str) -> dict:
    result = eval(python_expression, {"math": math, "random": random})
    logger.info("Calculating formula: %s, result: %s", python_expression, result)
    return {"success": True, "result": result}
