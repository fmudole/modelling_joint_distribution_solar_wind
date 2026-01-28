def calculate_average(values):
    total = 0
    for v in values:
        total += v
    return total / len(values)


def main():
    data = [1, 2, 3, 4, 5]
    avg = calculate_average(data)
    print("Average is", avg)


def calculate_variance(values):
    if not values:
        return 0

    mean = calculate_average(values)
    total = 0
    for v in values:
        total += (v - mean) ** 2

    return total / len(values)

main()
