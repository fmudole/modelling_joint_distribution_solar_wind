def calculate_average(values):
    total = 0
    for v in values:
        total += v
    return total / len(values)


def main():
    data = [1, 2, 3, 4, 5]
    avg = calculate_average(data)
    print("Average is", avg)


main()

