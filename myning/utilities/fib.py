def fibonacci(n: int) -> int:
    match n:
        case 1:
            return 0
        case 2:
            return 1
        case 3:
            return 3
        case 4:
            return 5
    a, b = 3, 5
    for _ in range(n - 4):
        a, b = b, a + b
    return b


def fibonacci_sum(n: int) -> int:
    if n <= 0:
        return 0
    base = [0, 1, 3, 5]
    total = sum(base[:n])
    if n <= 4:
        return total
    a, b = 3, 5
    for _ in range(n - 4):
        a, b = b, a + b
        total += b
    return total
