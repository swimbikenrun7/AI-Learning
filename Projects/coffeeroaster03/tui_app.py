import uuid

from textual.app import App, ComposeResult
from textual.containers import Horizontal, Vertical, VerticalScroll
from textual.screen import Screen
from textual.widgets import Button, DataTable, Footer, Header, Input, Label, Static

import calculations as calc
from data_persistence import (
    load_roast_profiles,
    load_roast_records,
    save_roast_profiles,
    save_roast_records,
)
from validators import (
    validate_bean_name,
    validate_date,
    validate_finished_weight,
    validate_first_crack,
    validate_green_weight,
    validate_profile_name,
    validate_roast_time,
    validate_temperature,
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
            Button("View and edit roast profiles", id="roast_profiles"),
            Button("Exit", id="exit"),
            id="menu",
        )
        yield Footer()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "add_roast":
            self.app.push_screen(SelectProfileScreen())
        elif event.button.id == "view_roasts":
            self.app.push_screen(ViewRoastsScreen())
        elif event.button.id == "roast_profiles":
            self.app.push_screen(RoastProfilesMenuScreen())
        elif event.button.id == "exit":
            self.app.exit()


class AddRoastScreen(Screen):
    def __init__(self, profile_id, profile_data):
        super().__init__()
        self.profile_id = profile_id
        self.profile_data = profile_data

    def compose(self) -> ComposeResult:
        yield Header()
        target_temps = calc.fill_forward(self.profile_data.get("temps", [None] * 12))
        fields = [
            Label("Date (MM/DD/YYYY)"),
            Input(placeholder="MM/DD/YYYY", id="date"),
            Label("Bean name"),
            Input(placeholder="Bean name", id="bean_name"),
            Label("Green weight (g)"),
            Input(placeholder="Green weight", id="green_weight"),
            Label(f"Roast profile: {self.profile_data.get('name', '')}"),
            Horizontal(
                Static("Time", classes="temp_cell"),
                Static("Actual (°F)", classes="temp_cell"),
                Static("Target (°F)", classes="temp_cell"),
                classes="temp_row",
            ),
        ]
        for minute in range(1, 13):
            target = target_temps[minute - 1]
            fields.append(
                Horizontal(
                    Static(f"{minute}:00", classes="temp_cell"),
                    Input(
                        placeholder="°F (optional)",
                        id=f"actual_temp_{minute}",
                        classes="temp_input",
                    ),
                    Static(
                        "-" if target is None else f"{target:g}",
                        id=f"target_temp_{minute}",
                        classes="temp_cell",
                    ),
                    classes="temp_row",
                )
            )
        fields += [
            Label("Time of first crack (MM:SS)"),
            Input(placeholder="MM:SS", id="first_crack"),
            Label("Total roast time (MM:SS)"),
            Input(placeholder="MM:SS", id="roast_time"),
            Label("Finished weight (g)"),
            Input(placeholder="Finished weight", id="finished_weight"),
            Static("", id="error"),
            Button("Submit", id="submit", variant="primary"),
            Button("Cancel", id="cancel"),
        ]
        yield VerticalScroll(*fields, id="form")
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
            entered_actual_temps = [
                validate_temperature(
                    self.query_one(f"#actual_temp_{minute}", Input).value
                )
                for minute in range(1, 13)
            ]
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

        target_temps = calc.fill_forward(self.profile_data.get("temps", [None] * 12))
        actual_temps = calc.resolve_actual_temps(
            entered_actual_temps, total_roast_time
        )

        new_record = {
            "date": date,
            "bean_name": bean_name,
            "green_weight": green_weight,
            "finished_weight": finished_weight,
            "total_roast_time": total_roast_time,
            "time_of_first_crack": time_of_first_crack,
            "roast_profile_id": self.profile_id,
            "target_temps": target_temps,
            "actual_temps": actual_temps,
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


class SelectProfileScreen(Screen):
    def compose(self) -> ComposeResult:
        yield Header()
        if self.app.roast_profiles:
            yield DataTable(id="select_profile_table", cursor_type="row")
            yield Button("Back", id="back")
        else:
            yield Vertical(
                Static(
                    "No roast profiles exist yet. Add one to start a roast.",
                    id="no_profiles_message",
                ),
                Button("Add new profile", id="add_profile"),
                Button("Back", id="back"),
                id="menu",
            )
        yield Footer()

    def on_mount(self) -> None:
        if self.app.roast_profiles:
            table = self.query_one("#select_profile_table", DataTable)
            table.add_columns("Profile name")
            for profile_id, profile in self.app.roast_profiles.items():
                table.add_row(profile["name"], key=profile_id)

    def on_data_table_row_selected(self, event: DataTable.RowSelected) -> None:
        profile_id = event.row_key.value
        profile_data = self.app.roast_profiles[profile_id]
        self.app.pop_screen()
        self.app.push_screen(
            AddRoastScreen(profile_id=profile_id, profile_data=profile_data)
        )

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "add_profile":
            self.app.pop_screen()
            self.app.push_screen(AddEditProfileScreen())
        elif event.button.id == "back":
            self.app.pop_screen()


class RoastProfilesMenuScreen(Screen):
    def compose(self) -> ComposeResult:
        yield Header()
        yield Vertical(
            Button("Add new profile", id="add_profile"),
            Button("View & edit profiles", id="view_profiles"),
            Button("Back", id="back"),
            id="menu",
        )
        yield Footer()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "add_profile":
            self.app.push_screen(AddEditProfileScreen())
        elif event.button.id == "view_profiles":
            self.app.push_screen(ProfileListScreen())
        elif event.button.id == "back":
            self.app.pop_screen()


class AddEditProfileScreen(Screen):
    def __init__(self, profile_id=None, profile_data=None):
        super().__init__()
        self.profile_id = profile_id
        self.profile_data = profile_data or {"name": "", "temps": [None] * 12}

    def compose(self) -> ComposeResult:
        yield Header()
        fields = [
            Label("Profile name"),
            Input(
                placeholder="Profile name",
                id="profile_name",
                value=self.profile_data.get("name", ""),
            ),
        ]
        temps = self.profile_data.get("temps", [None] * 12)
        for minute in range(1, 13):
            temp = temps[minute - 1] if minute - 1 < len(temps) else None
            fields.append(Label(f"{minute}:00 target temp (°F)"))
            fields.append(
                Input(
                    placeholder="°F (optional)",
                    id=f"temp_{minute}",
                    value="" if temp is None else str(temp),
                )
            )
        fields.append(Static("", id="error"))
        fields.append(Button("Submit", id="submit", variant="primary"))
        fields.append(Button("Cancel", id="cancel"))
        yield VerticalScroll(*fields, id="profile_form")
        yield Footer()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "cancel":
            self.app.pop_screen()
        elif event.button.id == "submit":
            self._submit()

    def _submit(self) -> None:
        error_widget = self.query_one("#error", Static)
        try:
            name = validate_profile_name(self.query_one("#profile_name", Input).value)
            temps = [
                validate_temperature(self.query_one(f"#temp_{minute}", Input).value)
                for minute in range(1, 13)
            ]
        except ValueError as error:
            error_widget.update(str(error))
            return

        profile_id = self.profile_id or str(uuid.uuid4())
        self.app.roast_profiles[profile_id] = {"name": name, "temps": temps}
        save_roast_profiles(self.app.roast_profiles)
        self.notify("Roast profile saved.")
        self.app.pop_screen()


class ProfileListScreen(Screen):
    def compose(self) -> ComposeResult:
        yield Header()
        yield DataTable(id="profile_table", cursor_type="row")
        yield Button("Back", id="back")
        yield Footer()

    def on_mount(self) -> None:
        table = self.query_one("#profile_table", DataTable)
        table.add_columns("Profile name")
        for profile_id, profile in self.app.roast_profiles.items():
            table.add_row(profile["name"], key=profile_id)

    def on_data_table_row_selected(self, event: DataTable.RowSelected) -> None:
        profile_id = event.row_key.value
        profile_data = self.app.roast_profiles[profile_id]
        self.app.push_screen(
            AddEditProfileScreen(profile_id=profile_id, profile_data=profile_data)
        )

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "back":
            self.app.pop_screen()


class RoastLoggerApp(App):
    CSS = """
    #menu, #profile_form {
        width: 60;
        margin: 1 2;
    }
    #form {
        width: 64;
        margin: 1 2;
    }
    #error {
        color: red;
        margin-bottom: 1;
    }
    .temp_row {
        height: 3;
    }
    .temp_cell {
        width: 18;
        content-align: left middle;
    }
    .temp_input {
        width: 24;
    }
    """

    def __init__(self, roast_records, roast_profiles=None):
        super().__init__()
        self.roast_records = roast_records
        self.roast_profiles = roast_profiles if roast_profiles is not None else {}

    def on_mount(self) -> None:
        self.push_screen(MainScreen())


def main():
    roast_records = load_roast_records()
    roast_profiles = load_roast_profiles()
    RoastLoggerApp(roast_records, roast_profiles).run()


if __name__ == "__main__":
    main()
