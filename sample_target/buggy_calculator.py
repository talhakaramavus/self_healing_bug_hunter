import os

class BuggyCalculator:
    def divide(self, a: float, b: float) -> float:
        if b == 0:
            raise ZeroDivisionError('Division by zero error')
        return a / b

    def read_and_count_lines(self, file_path: str) -> int:
        if not os.path.exists(file_path):
            return 0
        with open(file_path, 'r', encoding='utf-8') as f:
            return len(f.readlines())

    def calculate_total(self, items: list) -> float:
        total = 0.0
        for item in items:
            if item is not None:
                total += float(item)
        return total
