import uuid

import calculations as calc
from data_persistence import count_roasts, load_roast_records, save_roast_records
from user_input import (
    get_bean_name,
    get_date,
    get_finished_weight,
    get_green_weight,
    get_roast_time,
    get_time_of_first_crack,
)

ROAST_RECORDS = load_roast_records()


def display_menu():
    print("1. Add roast")
    print("2. View roasts")
    print("3. Count roasts")
    print("4. Exit")


def add_roast():
    date = get_date()
    bean_name = get_bean_name()
    green_weight = get_green_weight()
    finished_weight = get_finished_weight(green_weight)
    total_roast_time = get_roast_time()
    time_of_first_crack = get_time_of_first_crack(total_roast_time)

    new_record = {
        "date": date,
        "bean_name": bean_name,
        "green_weight": green_weight,
        "finished_weight": finished_weight,
        "total_roast_time": total_roast_time,
        "time_of_first_crack": time_of_first_crack,
    }

    record_id = str(uuid.uuid4())
    ROAST_RECORDS[record_id] = new_record
    save_roast_records(ROAST_RECORDS)
    print("Roast added successfully.")


ROAST_TABLE_COLUMNS = [
    ("Date", 10, "<"),
    ("Bean Name", 15, "<"),
    ("Green (g)", 9, ">"),
    ("Finished (g)", 12, ">"),
    ("Roast Time (s)", 14, ">"),
    ("1st Crack (s)", 13, ">"),
    ("Weight Loss (%)", 15, ">"),
    ("Dev Time (s)", 12, ">"),
    ("Classification", 15, "<"),
]


def view_roasts():
    header = " | ".join(
        f"{name:{align}{width}}" for name, width, align in ROAST_TABLE_COLUMNS
    )
    print(header)
    print("-" * len(header))

    for _, record in ROAST_RECORDS.items():
        weight_loss = calc.calculate_weight_loss(
            record['green_weight'], record['finished_weight']
        )
        development_time = calc.calculate_development_time(
            record['total_roast_time'], record['time_of_first_crack']
        )
        roast_classification = calc.classify_roast(weight_loss)

        row = [
            record['date'],
            record['bean_name'],
            f"{record['green_weight']:.1f}",
            f"{record['finished_weight']:.1f}",
            record['total_roast_time'],
            record['time_of_first_crack'],
            f"{weight_loss:.2f}",
            development_time,
            roast_classification,
        ]
        print(
            " | ".join(
                f"{value:{align}{width}}"
                for value, (_, width, align) in zip(row, ROAST_TABLE_COLUMNS)
            )
        )


def main():
    while True:
        display_menu()
        choice = input("Enter your choice (1/2/3/4): ")

        if choice == "1":
            add_roast()
        elif choice == "2":
            view_roasts()
        elif choice == "3":
            total_roasts = count_roasts()
            print(f"Total number of stored roasts: {total_roasts}")
        elif choice == "4":
            break
        else:
            print("Invalid choice. Please try again.")


if __name__ == "__main__":
    main()