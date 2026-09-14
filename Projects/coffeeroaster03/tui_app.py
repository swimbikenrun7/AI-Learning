import uuid

from textual.app import App, ComposeResult
from textual.containers import Vertical
from textual.screen import Screen
from textual.widgets import Button, DataTable, Footer, Header, Input, Label, Static

import calculations as calc
from data_persistence import load_roast_records, save_roast_records
from validators import (
    validate_bean_name,
    validate_date,
    validate_finished_weight,
    validate_first_crack,
    validate_green_weight,
    validate_roast_time,
)

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


class MainScreen(Screen):
    def compose(self) -> ComposeResult:
        yield Header()
        yield Vertical(
            Button("Add roast", id="add_roast"),
            Button("View roasts", id="view_roasts"),
            Button("Exit", id="exit"),
            id="menu",
        )
        yield Footer()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "add_roast":
            self.app.push_screen(AddRoastScreen())
        elif event.button.id == "view_roasts":
            self.app.push_screen(ViewRoastsScreen())
        elif event.button.id == "exit":
            self.app.exit()


class AddRoastScreen(Screen):
    def compose(self) -> ComposeResult:
        yield Header()
        yield Vertical(
            Label("Date (MM/DD/YYYY)"),
            Input(placeholder="MM/DD/YYYY", id="date"),
            Label("Bean name"),
            Input(placeholder="Bean name", id="bean_name"),
            Label("Green weight (g)"),
            Input(placeholder="Green weight", id="green_weight"),
            Label("Time of first crack (MM:SS)"),
            Input(placeholder="MM:SS", id="first_crack"),
            Label("Total roast time (MM:SS)"),
            Input(placeholder="MM:SS", id="roast_time"),
            Label("Finished weight (g)"),
            Input(placeholder="Finished weight", id="finished_weight"),
            Static("", id="error"),
            Button("Submit", id="submit", variant="primary"),
            Button("Cancel", id="cancel"),
            id="form",
        )
        yield Footer()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "cancel":
            self.app.pop_screen()
        elif event.button.id == "submit":
            self._submit()

    def _submit(self) -> None:
        error_widget = self.query_one("#error", Static)
        try:
            date = validate_date(self.query_one("#date", Input).value)
            bean_name = validate_bean_name(self.query_one("#bean_name", Input).value)
            green_weight = validate_green_weight(
                self.query_one("#green_weight", Input).value
            )
            total_roast_time = validate_roast_time(
                self.query_one("#roast_time", Input).value
            )
            time_of_first_crack = validate_first_crack(
                self.query_one("#first_crack", Input).value, total_roast_time
            )
            finished_weight = validate_finished_weight(
                self.query_one("#finished_weight", Input).value, green_weight
            )
        except ValueError as error:
            error_widget.update(str(error))
            return

        new_record = {
            "date": date,
            "bean_name": bean_name,
            "green_weight": green_weight,
            "finished_weight": finished_weight,
            "total_roast_time": total_roast_time,
            "time_of_first_crack": time_of_first_crack,
        }
        record_id = str(uuid.uuid4())
        self.app.roast_records[record_id] = new_record
        save_roast_records(self.app.roast_records)
        self.notify("Roast added successfully.")
        self.app.pop_screen()


class ViewRoastsScreen(Screen):
    def compose(self) -> ComposeResult:
        yield Header()
        yield DataTable(id="roast_table")
        yield Button("Back", id="back")
        yield Footer()

    def on_mount(self) -> None:
        table = self.query_one("#roast_table", DataTable)
        table.add_columns(*(name for name, _, _ in ROAST_TABLE_COLUMNS))
        for record in self.app.roast_records.values():
            weight_loss = calc.calculate_weight_loss(
                record["green_weight"], record["finished_weight"]
            )
            development_time = calc.calculate_development_time(
                record["total_roast_time"], record["time_of_first_crack"]
            )
            roast_classification = calc.classify_roast(weight_loss)
            table.add_row(
                record["date"],
                record["bean_name"],
                f"{record['green_weight']:.1f}",
                f"{record['finished_weight']:.1f}",
                record["total_roast_time"],
                record["time_of_first_crack"],
                f"{weight_loss:.2f}",
                development_time,
                roast_classification,
            )

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "back":
            self.app.pop_screen()


class RoastLoggerApp(App):
    CSS = """
    #menu, #form {
        width: 60;
        margin: 1 2;
    }
    #error {
        color: red;
        margin-bottom: 1;
    }
    """

    def __init__(self, roast_records):
        super().__init__()
        self.roast_records = roast_records

    def on_mount(self) -> None:
        self.push_screen(MainScreen())


def main():
    roast_records = load_roast_records()
    RoastLoggerApp(roast_records).run()


if __name__ == "__main__":
    main()
