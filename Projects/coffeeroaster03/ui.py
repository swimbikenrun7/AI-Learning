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

    weight_loss = calc.calculate_weight_loss(green_weight, finished_weight)
    development_time = calc.calculate_development_time(
        total_roast_time, time_of_first_crack
    )
    roast_classification = calc.classify_roast(weight_loss)

    new_record = {
        "date": date,
        "bean_name": bean_name,
        "green_weight": green_weight,
        "finished_weight": finished_weight,
        "total_roast_time": total_roast_time,
        "time_of_first_crack": time_of_first_crack,
        "weight_loss": weight_loss,
        "development_time": development_time,
        "roast_classification": roast_classification
    }

    ROAST_RECORDS[date] = new_record
    save_roast_records(ROAST_RECORDS)
    print("Roast added successfully.")


def view_roasts():
    for date, record in ROAST_RECORDS.items():
        print(f"Date: {record['date']}")
        print(f"Bean Name: {record['bean_name']}")
        print(f"Green Weight: {record['green_weight']}g")
        print(f"Finished Weight: {record['finished_weight']}g")
        print(f"Total Roast Time: {record['total_roast_time']}s")
        print(f"Time of First Crack: {record['time_of_first_crack']}s")
        print(f"Weight Loss: {record['weight_loss']:.2f}%")
        print(f"Development Time: {record['development_time']}s")
        print(f"Roast Classification: {record['roast_classification']}")
        print("-" * 40)


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