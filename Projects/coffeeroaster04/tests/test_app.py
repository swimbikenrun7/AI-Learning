import unittest
from datetime import datetime, timedelta
from unittest import mock

from werkzeug.security import check_password_hash, generate_password_hash

import app

OWNER_EMAIL = "owner@example.com"

ROASTERS = {
    "zeta-9": {"name": "Zeta Roaster 9", "values": {}},
    "alpha-1": {"name": "Alpha Roaster 1", "values": {}},
}


def login(client, email=OWNER_EMAIL):
    with client.session_transaction() as sess:
        sess["user_email"] = email


class TestRoutes(unittest.TestCase):
    def setUp(self):
        self.records = {
            "record-1": {
                "date": "09/07/2026",
                "bean_name": "Mysore Nuggets",
                "green_weight": 202.3,
                "finished_weight": 175.2,
                "total_roast_time": 450,
                "time_of_first_crack": 375,
                "roast_profile_id": "profile-1",
                "target_temps": [320, 365, 400, 430, 445, 455, 460]
                + [None] * 5,
                "actual_temps": [320, 365, 400, 430, 445, 455, 460]
                + [None] * 5,
                "owner": OWNER_EMAIL,
            }
        }
        self.profiles = {
            "profile-1": {
                "name": "Test Profile",
                "temps": [None] * 12,
                "owner": OWNER_EMAIL,
            }
        }
        self.records_patcher = mock.patch.object(app, "roast_records", self.records)
        self.profiles_patcher = mock.patch.object(app, "roast_profiles", self.profiles)
        self.records_patcher.start()
        self.profiles_patcher.start()
        self.client = app.app.test_client()
        login(self.client)

    def tearDown(self):
        self.records_patcher.stop()
        self.profiles_patcher.stop()

    def test_home_offers_main_menu_buttons(self):
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        body = response.get_data(as_text=True)
        self.assertIn("Add roast", body)
        self.assertIn("View roasts", body)
        self.assertIn("View and edit roast profiles", body)

    def test_view_roasts_lists_records(self):
        response = self.client.get("/roasts")
        self.assertEqual(response.status_code, 200)
        body = response.get_data(as_text=True)
        self.assertIn("Mysore Nuggets", body)
        self.assertIn("Test Profile", body)
        self.assertIn("City Plus", body)

    def test_view_roasts_formats_times_as_mm_ss(self):
        response = self.client.get("/roasts")
        body = response.get_data(as_text=True)
        self.assertIn("<td>7:30</td>", body)  # total_roast_time: 450s
        self.assertIn("<td>6:15</td>", body)  # time_of_first_crack: 375s
        self.assertIn("<td>1:15</td>", body)  # development_time: 450 - 375 = 75s

    def test_roast_detail_shows_temps_and_chart(self):
        response = self.client.get("/roasts/record-1")
        self.assertEqual(response.status_code, 200)
        body = response.get_data(as_text=True)
        self.assertIn("Mysore Nuggets", body)
        self.assertIn("Test Profile", body)
        self.assertIn("temp-chart", body)
        self.assertIn("460", body)

    def test_roast_detail_missing_record_returns_404(self):
        response = self.client.get("/roasts/does-not-exist")
        self.assertEqual(response.status_code, 404)

    def test_roast_detail_shows_calculated_stats(self):
        response = self.client.get("/roasts/record-1")
        body = response.get_data(as_text=True)
        self.assertIn("13.40%", body)  # weight loss: (202.3-175.2)/202.3*100
        self.assertIn("City Plus", body)
        self.assertIn("1:15", body)  # development time: 450 - 375
        self.assertIn("16.7%", body)  # DTR: 75/450*100

    def test_export_roasts_returns_csv(self):
        response = self.client.get("/roasts/export")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.mimetype, "text/csv")
        body = response.get_data(as_text=True)
        self.assertIn("Date,Bean Name,Roast Profile", body)
        self.assertIn("Mysore Nuggets", body)
        self.assertIn("13.40", body)

    def test_export_roasts_excludes_other_owners(self):
        self.records["record-2"] = {**self.records["record-1"], "owner": "other@example.com"}
        response = self.client.get("/roasts/export")
        body = response.get_data(as_text=True)
        self.assertEqual(body.count("Mysore Nuggets"), 1)

    def test_roast_detail_includes_rate_of_rise_series(self):
        response = self.client.get("/roasts/record-1")
        body = response.get_data(as_text=True)
        self.assertIn("ror-chart", body)
        self.assertIn("[null, 45, 35, 30, 15, 10, 5, null, null, null, null, null]", body)

    def test_roast_detail_includes_target_rate_of_rise_series(self):
        self.records["record-1"]["target_temps"] = [300, 350, 400] + [None] * 9
        response = self.client.get("/roasts/record-1")
        body = response.get_data(as_text=True)
        self.assertIn("[null, 50, 50, null, null, null, null, null, null, null, null, null]", body)


class TestSelectProfile(unittest.TestCase):
    def setUp(self):
        self.client = app.app.test_client()
        login(self.client)

    def test_lists_existing_profiles(self):
        profiles = {
            "profile-1": {"name": "Test Profile", "temps": [None] * 12, "owner": OWNER_EMAIL}
        }
        with mock.patch.object(app, "roast_profiles", profiles):
            response = self.client.get("/roasts/new")
        self.assertEqual(response.status_code, 200)
        self.assertIn("Test Profile", response.get_data(as_text=True))

    def test_shows_message_when_no_profiles_exist(self):
        with mock.patch.object(app, "roast_profiles", {}):
            response = self.client.get("/roasts/new")
        self.assertEqual(response.status_code, 200)
        self.assertIn("No roast profiles exist yet", response.get_data(as_text=True))

    def test_lists_profiles_alphabetically(self):
        profiles = {
            "profile-1": {"name": "Zephyr Blend", "temps": [None] * 12, "owner": OWNER_EMAIL},
            "profile-2": {"name": "Amber Roast", "temps": [None] * 12, "owner": OWNER_EMAIL},
        }
        with mock.patch.object(app, "roast_profiles", profiles):
            response = self.client.get("/roasts/new")
        body = response.get_data(as_text=True)
        self.assertLess(body.index("Amber Roast"), body.index("Zephyr Blend"))

    def test_favorited_profiles_are_listed_before_the_rest(self):
        profiles = {
            "profile-1": {"name": "Amber Roast", "temps": [None] * 12, "owner": OWNER_EMAIL},
            "profile-2": {
                "name": "Zephyr Blend",
                "temps": [None] * 12,
                "favorite": True,
                "owner": OWNER_EMAIL,
            },
        }
        with mock.patch.object(app, "roast_profiles", profiles):
            response = self.client.get("/roasts/new")
        body = response.get_data(as_text=True)
        self.assertLess(body.index("Zephyr Blend"), body.index("Amber Roast"))

    def test_favorites_and_other_profiles_are_shown_as_separate_groups(self):
        profiles = {
            "profile-1": {"name": "Amber Roast", "temps": [None] * 12, "owner": OWNER_EMAIL},
            "profile-2": {
                "name": "Zephyr Blend",
                "temps": [None] * 12,
                "favorite": True,
                "owner": OWNER_EMAIL,
            },
        }
        with mock.patch.object(app, "roast_profiles", profiles):
            response = self.client.get("/roasts/new")
        body = response.get_data(as_text=True)
        self.assertIn("Favorites", body)
        self.assertIn("All other profiles", body)
        self.assertLess(body.index("Favorites"), body.index("Zephyr Blend"))
        self.assertLess(body.index("All other profiles"), body.index("Amber Roast"))

    def test_no_favorites_heading_omitted_when_none_favorited(self):
        profiles = {
            "profile-1": {"name": "Amber Roast", "temps": [None] * 12, "owner": OWNER_EMAIL},
        }
        with mock.patch.object(app, "roast_profiles", profiles):
            response = self.client.get("/roasts/new")
        body = response.get_data(as_text=True)
        self.assertNotIn("Favorites", body)
        self.assertIn(">Profiles<", body)

    def test_each_card_has_a_favorite_toggle_pointing_back_to_this_page(self):
        profiles = {
            "profile-1": {"name": "Amber Roast", "temps": [None] * 12, "owner": OWNER_EMAIL},
        }
        with mock.patch.object(app, "roast_profiles", profiles):
            response = self.client.get("/roasts/new")
        body = response.get_data(as_text=True)
        self.assertIn('action="/profiles/profile-1/favorite"', body)
        self.assertIn('name="next" value="/roasts/new"', body)

    def test_cards_show_each_profiles_roaster_name(self):
        profiles = {
            "profile-1": {
                "name": "Amber Roast",
                "roaster_id": "alpha-1",
                "favorite": True,
                "temps": [None] * 12,
                "owner": OWNER_EMAIL,
            },
            "profile-2": {
                "name": "Bold Roast",
                "roaster_id": "zeta-9",
                "temps": [None] * 12,
                "owner": OWNER_EMAIL,
            },
        }
        with mock.patch.object(app, "roast_profiles", profiles), mock.patch.object(
            app, "roasters", ROASTERS
        ):
            body = self.client.get("/roasts/new").get_data(as_text=True)
        self.assertIn('<span class="roaster-tag">Alpha Roaster 1</span>', body)
        self.assertIn('<span class="roaster-tag">Zeta Roaster 9</span>', body)

    def test_cards_omit_roaster_tag_when_profile_has_no_roaster(self):
        profiles = {
            "profile-1": {"name": "Amber Roast", "temps": [None] * 12, "owner": OWNER_EMAIL},
        }
        with mock.patch.object(app, "roast_profiles", profiles), mock.patch.object(
            app, "roasters", ROASTERS
        ):
            body = self.client.get("/roasts/new").get_data(as_text=True)
        self.assertNotIn('<span class="roaster-tag">', body)


class TestAddRoast(unittest.TestCase):
    def setUp(self):
        self.records = {}
        self.profiles = {
            "profile-1": {
                "name": "Test Profile",
                "temps": [320, 365, 400, 430, 445, 455, 460] + [None] * 5,
                "owner": OWNER_EMAIL,
            }
        }
        self.records_patcher = mock.patch.object(app, "roast_records", self.records)
        self.profiles_patcher = mock.patch.object(app, "roast_profiles", self.profiles)
        self.save_patcher = mock.patch.object(app, "save_roast_records")
        self.records_patcher.start()
        self.profiles_patcher.start()
        self.save_patcher.start()
        self.client = app.app.test_client()
        login(self.client)

    def tearDown(self):
        self.records_patcher.stop()
        self.profiles_patcher.stop()
        self.save_patcher.stop()

    def valid_form_data(self):
        data = {
            "date": "09/07/2026",
            "bean_name": "Ethiopia Yirgacheffe",
            "green_weight": "205",
            "first_crack": "06:15",
            "roast_time": "07:30",
            "finished_weight": "178",
        }
        entered = [320, 365, 400, 430, 445, 455, 460] + [""] * 5
        for minute, value in enumerate(entered, start=1):
            data[f"actual_temp_{minute}"] = "" if value == "" else str(value)
        return data

    def test_missing_profile_returns_404(self):
        response = self.client.get("/roasts/new/does-not-exist")
        self.assertEqual(response.status_code, 404)

    def test_get_form_shows_profile_target_temps(self):
        response = self.client.get("/roasts/new/profile-1")
        self.assertEqual(response.status_code, 200)
        body = response.get_data(as_text=True)
        self.assertIn("Test Profile", body)
        self.assertIn("460", body)

    def test_get_form_shows_the_profiles_roaster(self):
        self.profiles["profile-1"]["roaster_id"] = "alpha-1"
        with mock.patch.object(app, "roasters", ROASTERS):
            body = self.client.get("/roasts/new/profile-1").get_data(as_text=True)
        self.assertIn('<span class="roaster-tag">&middot; Alpha Roaster 1</span>', body)

    def test_get_form_omits_roaster_tag_when_profile_has_no_roaster(self):
        with mock.patch.object(app, "roasters", ROASTERS):
            body = self.client.get("/roasts/new/profile-1").get_data(as_text=True)
        self.assertNotIn('<span class="roaster-tag">', body)

    def test_post_valid_data_saves_record_and_redirects_to_detail(self):
        response = self.client.post(
            "/roasts/new/profile-1", data=self.valid_form_data()
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(len(self.records), 1)
        (record_id, record), = self.records.items()
        self.assertIn(f"/roasts/{record_id}", response.headers["Location"])
        self.assertEqual(record["bean_name"], "Ethiopia Yirgacheffe")
        self.assertEqual(record["roast_profile_id"], "profile-1")
        self.assertEqual(record["owner"], OWNER_EMAIL)
        self.assertEqual(
            record["target_temps"], [320, 365, 400, 430, 445, 455, 460] + [460] * 5
        )
        app.save_roast_records.assert_called_once_with(self.records)

    def test_post_valid_data_redirect_shows_chart(self):
        response = self.client.post(
            "/roasts/new/profile-1", data=self.valid_form_data(), follow_redirects=True
        )
        self.assertEqual(response.status_code, 200)
        body = response.get_data(as_text=True)
        self.assertIn("Ethiopia Yirgacheffe", body)
        self.assertIn("temp-chart", body)

    def test_post_invalid_field_shows_error_and_preserves_input(self):
        data = self.valid_form_data()
        data["green_weight"] = "50"  # below the 100g minimum
        response = self.client.post("/roasts/new/profile-1", data=data)
        self.assertEqual(response.status_code, 200)
        body = response.get_data(as_text=True)
        self.assertIn("Invalid input", body)
        self.assertIn("Ethiopia Yirgacheffe", body)  # other fields preserved
        self.assertEqual(self.records, {})

    def test_post_saves_optional_bean_metadata(self):
        data = self.valid_form_data()
        data["bean_origin"] = "Ethiopia"
        data["bean_variety"] = "Heirloom"
        data["bean_process"] = "Washed"
        self.client.post("/roasts/new/profile-1", data=data)
        (record,) = self.records.values()
        self.assertEqual(record["bean_origin"], "Ethiopia")
        self.assertEqual(record["bean_variety"], "Heirloom")
        self.assertEqual(record["bean_process"], "Washed")

    def test_post_without_bean_metadata_saves_empty_strings(self):
        self.client.post("/roasts/new/profile-1", data=self.valid_form_data())
        (record,) = self.records.values()
        self.assertEqual(record["bean_origin"], "")
        self.assertEqual(record["bean_variety"], "")
        self.assertEqual(record["bean_process"], "")


class TestCuppingNotes(unittest.TestCase):
    def setUp(self):
        self.records = {
            "record-1": {
                "date": "09/07/2026",
                "bean_name": "Mysore Nuggets",
                "green_weight": 202.3,
                "finished_weight": 175.2,
                "total_roast_time": 450,
                "time_of_first_crack": 375,
                "roast_profile_id": "profile-1",
                "target_temps": [320] * 12,
                "actual_temps": [320] * 12,
                "owner": OWNER_EMAIL,
            }
        }
        self.records_patcher = mock.patch.object(app, "roast_records", self.records)
        self.save_patcher = mock.patch.object(app, "save_roast_records")
        self.records_patcher.start()
        self.save_patcher.start()
        self.client = app.app.test_client()
        login(self.client)

    def tearDown(self):
        self.records_patcher.stop()
        self.save_patcher.stop()

    def test_saves_notes_and_rating_and_redirects(self):
        response = self.client.post(
            "/roasts/record-1/cupping",
            data={"cupping_notes": "Bright, floral, tea-like", "cupping_rating": "4"},
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.headers["Location"], "/roasts/record-1")
        self.assertEqual(
            self.records["record-1"]["cupping_notes"], "Bright, floral, tea-like"
        )
        self.assertEqual(self.records["record-1"]["cupping_rating"], 4)
        app.save_roast_records.assert_called_once_with(self.records)

    def test_rating_is_optional(self):
        self.client.post(
            "/roasts/record-1/cupping", data={"cupping_notes": "Needs more time"}
        )
        self.assertEqual(self.records["record-1"]["cupping_notes"], "Needs more time")
        self.assertIsNone(self.records["record-1"]["cupping_rating"])

    def test_out_of_range_rating_rejected(self):
        response = self.client.post(
            "/roasts/record-1/cupping",
            data={"cupping_notes": "x", "cupping_rating": "9"},
        )
        self.assertEqual(response.status_code, 400)

    def test_non_numeric_rating_rejected(self):
        response = self.client.post(
            "/roasts/record-1/cupping",
            data={"cupping_notes": "x", "cupping_rating": "great"},
        )
        self.assertEqual(response.status_code, 400)

    def test_missing_record_returns_404(self):
        response = self.client.post(
            "/roasts/does-not-exist/cupping", data={"cupping_notes": "x"}
        )
        self.assertEqual(response.status_code, 404)

    def test_other_owners_record_returns_404(self):
        self.records["record-1"]["owner"] = "other@example.com"
        response = self.client.post(
            "/roasts/record-1/cupping", data={"cupping_notes": "x"}
        )
        self.assertEqual(response.status_code, 404)

    def test_roast_detail_shows_saved_cupping_notes(self):
        self.records["record-1"]["cupping_notes"] = "Bright, floral"
        self.records["record-1"]["cupping_rating"] = 4
        response = self.client.get("/roasts/record-1")
        body = response.get_data(as_text=True)
        self.assertIn("Bright, floral", body)


class TestListProfiles(unittest.TestCase):
    def setUp(self):
        self.client = app.app.test_client()
        login(self.client)

    def test_lists_existing_profiles(self):
        profiles = {
            "profile-1": {"name": "Test Profile", "temps": [None] * 12, "owner": OWNER_EMAIL}
        }
        with mock.patch.object(app, "roast_profiles", profiles):
            response = self.client.get("/profiles")
        self.assertEqual(response.status_code, 200)
        self.assertIn("Test Profile", response.get_data(as_text=True))

    def test_shows_each_profiles_roaster_name_beside_the_profile_name(self):
        profiles = {
            "profile-1": {
                "name": "Test Profile",
                "roaster_id": "zeta-9",
                "temps": [None] * 12,
                "owner": OWNER_EMAIL,
            },
            "profile-2": {"name": "Other Profile", "temps": [None] * 12, "owner": OWNER_EMAIL},
        }
        with mock.patch.object(app, "roast_profiles", profiles), mock.patch.object(
            app, "roasters", ROASTERS
        ):
            body = self.client.get("/profiles").get_data(as_text=True)
        self.assertEqual(body.count('class="roaster-tag"'), 1)
        self.assertIn("Zeta Roaster 9", body)

    def test_shows_message_when_no_profiles_exist(self):
        with mock.patch.object(app, "roast_profiles", {}):
            response = self.client.get("/profiles")
        self.assertEqual(response.status_code, 200)
        self.assertIn("No roast profiles exist yet", response.get_data(as_text=True))

    def test_lists_profiles_alphabetically(self):
        profiles = {
            "profile-1": {"name": "Zephyr Blend", "temps": [None] * 12, "owner": OWNER_EMAIL},
            "profile-2": {"name": "Amber Roast", "temps": [None] * 12, "owner": OWNER_EMAIL},
        }
        with mock.patch.object(app, "roast_profiles", profiles):
            response = self.client.get("/profiles")
        body = response.get_data(as_text=True)
        self.assertLess(body.index("Amber Roast"), body.index("Zephyr Blend"))

    def test_favorited_profiles_are_listed_before_the_rest(self):
        profiles = {
            "profile-1": {"name": "Amber Roast", "temps": [None] * 12, "owner": OWNER_EMAIL},
            "profile-2": {
                "name": "Zephyr Blend",
                "temps": [None] * 12,
                "favorite": True,
                "owner": OWNER_EMAIL,
            },
        }
        with mock.patch.object(app, "roast_profiles", profiles):
            response = self.client.get("/profiles")
        body = response.get_data(as_text=True)
        self.assertLess(body.index("Zephyr Blend"), body.index("Amber Roast"))


class TestToggleProfileFavorite(unittest.TestCase):
    def setUp(self):
        self.profiles = {
            "profile-1": {"name": "Test Profile", "temps": [None] * 12, "owner": OWNER_EMAIL}
        }
        self.profiles_patcher = mock.patch.object(app, "roast_profiles", self.profiles)
        self.save_patcher = mock.patch.object(app, "save_roast_profiles")
        self.profiles_patcher.start()
        self.save_patcher.start()
        self.client = app.app.test_client()
        login(self.client)

    def tearDown(self):
        self.profiles_patcher.stop()
        self.save_patcher.stop()

    def test_missing_profile_returns_404(self):
        response = self.client.post("/profiles/does-not-exist/favorite")
        self.assertEqual(response.status_code, 404)

    def test_toggles_favorite_on_then_off_and_redirects(self):
        response = self.client.post("/profiles/profile-1/favorite")
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.headers["Location"], "/profiles")
        self.assertTrue(self.profiles["profile-1"]["favorite"])

        self.client.post("/profiles/profile-1/favorite")
        self.assertFalse(self.profiles["profile-1"]["favorite"])
        app.save_roast_profiles.assert_called_with(self.profiles)

    def test_redirects_back_to_select_profile_when_toggled_from_there(self):
        response = self.client.post(
            "/profiles/profile-1/favorite", data={"next": "/roasts/new"}
        )
        self.assertEqual(response.headers["Location"], "/roasts/new")

    def test_ignores_untrusted_next_and_falls_back_to_profiles(self):
        response = self.client.post(
            "/profiles/profile-1/favorite", data={"next": "https://evil.example/"}
        )
        self.assertEqual(response.headers["Location"], "/profiles")


class TestAddEditProfile(unittest.TestCase):
    def setUp(self):
        self.profiles = {
            "profile-1": {
                "name": "Existing Profile",
                "temps": [320, 365, 400] + [None] * 9,
                "owner": OWNER_EMAIL,
            }
        }
        self.profiles_patcher = mock.patch.object(app, "roast_profiles", self.profiles)
        self.save_patcher = mock.patch.object(app, "save_roast_profiles")
        self.profiles_patcher.start()
        self.save_patcher.start()
        self.client = app.app.test_client()
        login(self.client)

    def tearDown(self):
        self.profiles_patcher.stop()
        self.save_patcher.stop()

    def blank_temp_form(self, **overrides):
        data = {f"temp_{minute}": "" for minute in range(1, 13)}
        data.update(overrides)
        return data

    def test_new_profile_shows_blank_form(self):
        response = self.client.get("/profiles/new")
        self.assertEqual(response.status_code, 200)
        self.assertIn("Add roast profile", response.get_data(as_text=True))

    def test_edit_profile_missing_returns_404(self):
        response = self.client.get("/profiles/does-not-exist")
        self.assertEqual(response.status_code, 404)

    def test_edit_profile_shows_existing_values(self):
        response = self.client.get("/profiles/profile-1")
        self.assertEqual(response.status_code, 200)
        body = response.get_data(as_text=True)
        self.assertIn("Existing Profile", body)
        self.assertIn('value="320"', body)

    def test_post_new_profile_creates_and_redirects(self):
        data = self.blank_temp_form(
            name="Brand New Profile", temp_1="300", temp_2="340", temp_3="380"
        )
        response = self.client.post("/profiles/new", data=data)
        self.assertEqual(response.status_code, 302)
        self.assertIn("/profiles", response.headers["Location"])
        new_profiles = [
            profile
            for profile in self.profiles.values()
            if profile["name"] == "Brand New Profile"
        ]
        self.assertEqual(len(new_profiles), 1)
        self.assertEqual(new_profiles[0]["temps"][:3], [300, 340, 380])
        self.assertEqual(new_profiles[0]["owner"], OWNER_EMAIL)
        app.save_roast_profiles.assert_called_once_with(self.profiles)

    def test_post_new_profile_invalid_shows_error_and_preserves_input(self):
        data = self.blank_temp_form(name="", temp_1="999")
        response = self.client.post("/profiles/new", data=data)
        self.assertEqual(response.status_code, 200)
        body = response.get_data(as_text=True)
        self.assertIn("Profile name is required", body)
        self.assertIn('value="999"', body)

    def test_post_edit_updates_existing_profile_in_place(self):
        data = self.blank_temp_form(name="Updated Name")
        response = self.client.post("/profiles/profile-1", data=data)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(set(self.profiles), {"profile-1"})
        self.assertEqual(self.profiles["profile-1"]["name"], "Updated Name")

    def test_post_new_profile_defaults_to_not_favorite(self):
        data = self.blank_temp_form(name="Brand New Profile")
        self.client.post("/profiles/new", data=data)
        new_profile = next(
            profile
            for profile in self.profiles.values()
            if profile["name"] == "Brand New Profile"
        )
        self.assertFalse(new_profile["favorite"])

    def test_form_lists_roasters_alphabetically_with_a_blank_default(self):
        with mock.patch.object(app, "roasters", ROASTERS):
            body = self.client.get("/profiles/new").get_data(as_text=True)
        self.assertIn('name="roaster_id"', body)
        self.assertIn("No roaster selected", body)
        self.assertLess(body.index("Alpha Roaster 1"), body.index("Zeta Roaster 9"))

    def test_roaster_dropdown_sits_above_the_wizard_and_is_tied_to_the_form(self):
        with mock.patch.object(app, "roasters", ROASTERS):
            body = self.client.get("/profiles/new").get_data(as_text=True)
        self.assertIn('<form method="post" id="profile-form">', body)
        self.assertIn('form="profile-form"', body)
        self.assertLess(body.index('name="roaster_id"'), body.index('id="wizard-panel"'))

    def test_edit_form_preselects_the_saved_roaster(self):
        self.profiles["profile-1"]["roaster_id"] = "zeta-9"
        with mock.patch.object(app, "roasters", ROASTERS):
            body = self.client.get("/profiles/profile-1").get_data(as_text=True)
        self.assertIn('<option value="zeta-9" selected>', body)
        self.assertNotIn('<option value="alpha-1" selected>', body)

    def test_post_new_profile_saves_selected_roaster(self):
        data = self.blank_temp_form(name="With Roaster", roaster_id="alpha-1")
        with mock.patch.object(app, "roasters", ROASTERS):
            response = self.client.post("/profiles/new", data=data)
        self.assertEqual(response.status_code, 302)
        saved = next(p for p in self.profiles.values() if p["name"] == "With Roaster")
        self.assertEqual(saved["roaster_id"], "alpha-1")

    def test_post_new_profile_without_roaster_stores_none(self):
        data = self.blank_temp_form(name="No Roaster", roaster_id="")
        with mock.patch.object(app, "roasters", ROASTERS):
            self.client.post("/profiles/new", data=data)
        saved = next(p for p in self.profiles.values() if p["name"] == "No Roaster")
        self.assertIsNone(saved["roaster_id"])

    def test_post_edit_can_change_the_roaster(self):
        self.profiles["profile-1"]["roaster_id"] = "alpha-1"
        data = self.blank_temp_form(name="Existing Profile", roaster_id="zeta-9")
        with mock.patch.object(app, "roasters", ROASTERS):
            self.client.post("/profiles/profile-1", data=data)
        self.assertEqual(self.profiles["profile-1"]["roaster_id"], "zeta-9")

    def test_post_unknown_roaster_shows_error_and_does_not_save(self):
        data = self.blank_temp_form(name="Bad Roaster", roaster_id="not-a-roaster")
        with mock.patch.object(app, "roasters", ROASTERS):
            response = self.client.post("/profiles/new", data=data)
        self.assertEqual(response.status_code, 200)
        self.assertIn("Choose a roaster from the list", response.get_data(as_text=True))
        self.assertEqual(set(self.profiles), {"profile-1"})

    def test_editing_profile_preserves_favorite_flag(self):
        self.profiles["profile-1"]["favorite"] = True
        data = self.blank_temp_form(name="Updated Name")
        self.client.post("/profiles/profile-1", data=data)
        self.assertTrue(self.profiles["profile-1"]["favorite"])

    def test_editing_profile_does_not_alter_saved_roast_snapshot(self):
        saved_target_temps = [320, 365, 400] + [None] * 9
        roast_records = {
            "record-1": {
                "roast_profile_id": "profile-1",
                "target_temps": list(saved_target_temps),
                "owner": OWNER_EMAIL,
            }
        }
        with mock.patch.object(app, "roast_records", roast_records):
            data = self.blank_temp_form(
                name="Changed Targets", **{f"temp_{m}": "999" for m in range(1, 13)}
            )
            self.client.post("/profiles/profile-1", data=data)
            self.assertEqual(
                roast_records["record-1"]["target_temps"], saved_target_temps
            )


class TestDeleteRoast(unittest.TestCase):
    def setUp(self):
        self.records = {
            "record-1": {
                "date": "09/07/2026",
                "bean_name": "Mysore Nuggets",
                "roast_profile_id": "profile-1",
                "target_temps": [320] + [None] * 11,
                "actual_temps": [320] + [None] * 11,
                "owner": OWNER_EMAIL,
            }
        }
        self.records_patcher = mock.patch.object(app, "roast_records", self.records)
        self.save_patcher = mock.patch.object(app, "save_roast_records")
        self.records_patcher.start()
        self.save_patcher.start()
        self.client = app.app.test_client()
        login(self.client)

    def tearDown(self):
        self.records_patcher.stop()
        self.save_patcher.stop()

    def test_missing_record_returns_404(self):
        response = self.client.get("/roasts/does-not-exist/delete")
        self.assertEqual(response.status_code, 404)

    def test_get_shows_confirmation(self):
        response = self.client.get("/roasts/record-1/delete")
        self.assertEqual(response.status_code, 200)
        body = response.get_data(as_text=True)
        self.assertIn("Mysore Nuggets", body)
        self.assertIn("cannot be undone", body)
        self.assertIn("record-1", self.records)  # not deleted yet

    def test_post_deletes_record_and_redirects(self):
        response = self.client.post("/roasts/record-1/delete")
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.headers["Location"], "/roasts")
        self.assertNotIn("record-1", self.records)
        app.save_roast_records.assert_called_once_with(self.records)


class TestDeleteProfile(unittest.TestCase):
    def setUp(self):
        self.profiles = {
            "profile-1": {"name": "Test Profile", "temps": [None] * 12, "owner": OWNER_EMAIL}
        }
        self.records = {
            "record-1": {
                "roast_profile_id": "profile-1",
                "target_temps": [320, 365, 400] + [None] * 9,
                "owner": OWNER_EMAIL,
            }
        }
        self.profiles_patcher = mock.patch.object(app, "roast_profiles", self.profiles)
        self.records_patcher = mock.patch.object(app, "roast_records", self.records)
        self.save_patcher = mock.patch.object(app, "save_roast_profiles")
        self.profiles_patcher.start()
        self.records_patcher.start()
        self.save_patcher.start()
        self.client = app.app.test_client()
        login(self.client)

    def tearDown(self):
        self.profiles_patcher.stop()
        self.records_patcher.stop()
        self.save_patcher.stop()

    def test_missing_profile_returns_404(self):
        response = self.client.get("/profiles/does-not-exist/delete")
        self.assertEqual(response.status_code, 404)

    def test_get_shows_confirmation_with_referencing_roast_count(self):
        response = self.client.get("/profiles/profile-1/delete")
        self.assertEqual(response.status_code, 200)
        body = response.get_data(as_text=True)
        self.assertIn("Test Profile", body)
        self.assertIn("1 saved roast", body)
        self.assertIn("profile-1", self.profiles)  # not deleted yet

    def test_post_deletes_profile_and_redirects(self):
        response = self.client.post("/profiles/profile-1/delete")
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.headers["Location"], "/profiles")
        self.assertNotIn("profile-1", self.profiles)
        app.save_roast_profiles.assert_called_once_with(self.profiles)

    def test_deleting_profile_leaves_referencing_roast_snapshot_untouched(self):
        original_target_temps = list(self.records["record-1"]["target_temps"])
        self.client.post("/profiles/profile-1/delete")
        self.assertEqual(
            self.records["record-1"]["target_temps"], original_target_temps
        )
        self.assertIn("record-1", self.records)


class TestSignup(unittest.TestCase):
    # Signing up while `users` is empty triggers the first-account seed-data
    # migration (see app.signup), which touches roast_records/roast_profiles
    # and calls their save functions - every test here must patch those too,
    # not just users/save_users, or a signup test will silently write to the
    # real data/*.json files on disk.
    def setUp(self):
        self.users = {}
        self.records = {}
        self.profiles = {}
        self.users_patcher = mock.patch.object(app, "users", self.users)
        self.records_patcher = mock.patch.object(app, "roast_records", self.records)
        self.profiles_patcher = mock.patch.object(app, "roast_profiles", self.profiles)
        self.save_users_patcher = mock.patch.object(app, "save_users")
        self.save_records_patcher = mock.patch.object(app, "save_roast_records")
        self.save_profiles_patcher = mock.patch.object(app, "save_roast_profiles")
        self.send_email_patcher = mock.patch.object(app, "send_email")
        self.users_patcher.start()
        self.records_patcher.start()
        self.profiles_patcher.start()
        self.save_users_patcher.start()
        self.save_records_patcher.start()
        self.save_profiles_patcher.start()
        self.send_email_patcher.start()
        self.client = app.app.test_client()

    def tearDown(self):
        self.users_patcher.stop()
        self.records_patcher.stop()
        self.profiles_patcher.stop()
        self.save_users_patcher.stop()
        self.save_records_patcher.stop()
        self.save_profiles_patcher.stop()
        self.send_email_patcher.stop()

    def signup_data(self, **overrides):
        data = {
            "email": "new@example.com",
            "password": "longenough1",
            "confirm": "longenough1",
        }
        data.update(overrides)
        return data

    def test_signup_creates_account_logs_in_and_redirects_home(self):
        response = self.client.post("/signup", data=self.signup_data(email="New@Example.com"))
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.headers["Location"], "/")
        self.assertIn("new@example.com", self.users)  # normalized to lowercase
        with self.client.session_transaction() as sess:
            self.assertEqual(sess["user_email"], "new@example.com")
        app.save_users.assert_called_once_with(self.users)

    def test_signup_creates_unverified_account_and_sends_verification_email(self):
        self.client.post("/signup", data=self.signup_data())
        user = self.users["new@example.com"]
        self.assertFalse(user["email_verified"])
        self.assertTrue(user["verify_token"])
        app.send_email.assert_called_once()
        to_address, subject, body = app.send_email.call_args[0]
        self.assertEqual(to_address, "new@example.com")
        self.assertIn("verify-email", body)
        self.assertIn(user["verify_token"], body)

    def test_signup_redirects_to_safe_next(self):
        response = self.client.post("/signup", data=self.signup_data(next="/roasts"))
        self.assertEqual(response.headers["Location"], "/roasts")

    def test_signup_ignores_unsafe_next(self):
        response = self.client.post(
            "/signup", data=self.signup_data(next="https://evil.example/")
        )
        self.assertEqual(response.headers["Location"], "/")

    def test_signup_rejects_short_password(self):
        response = self.client.post(
            "/signup", data=self.signup_data(password="short1", confirm="short1")
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn("at least 8 characters", response.get_data(as_text=True))
        self.assertEqual(self.users, {})

    def test_signup_rejects_invalid_email(self):
        response = self.client.post("/signup", data=self.signup_data(email="not-an-email"))
        self.assertEqual(response.status_code, 200)
        self.assertIn("valid email", response.get_data(as_text=True))

    def test_signup_rejects_mismatched_passwords(self):
        response = self.client.post("/signup", data=self.signup_data(confirm="different1"))
        self.assertIn("do not match", response.get_data(as_text=True))

    def test_signup_rejects_duplicate_email_case_insensitively(self):
        self.users["dup@example.com"] = {"password_hash": "x", "created_at": "now"}
        response = self.client.post("/signup", data=self.signup_data(email="Dup@Example.com"))
        self.assertIn("already exists", response.get_data(as_text=True))

    def test_first_signup_migrates_ownerless_seed_data(self):
        self.records["r1"] = {"bean_name": "Seed"}
        self.profiles["p1"] = {"name": "Seed Profile"}
        self.client.post("/signup", data=self.signup_data(email="first@example.com"))
        self.assertEqual(self.records["r1"]["owner"], "first@example.com")
        self.assertEqual(self.profiles["p1"]["owner"], "first@example.com")

    def test_second_signup_does_not_touch_already_owned_data(self):
        self.users["existing@example.com"] = {"password_hash": "x", "created_at": "now"}
        self.records["r1"] = {"bean_name": "Seed", "owner": "existing@example.com"}
        self.client.post("/signup", data=self.signup_data(email="second@example.com"))
        self.assertEqual(self.records["r1"]["owner"], "existing@example.com")
        app.save_roast_records.assert_not_called()


class TestLogin(unittest.TestCase):
    def setUp(self):
        self.users = {
            "user@example.com": {
                "password_hash": generate_password_hash("correct-password"),
                "created_at": "now",
            }
        }
        self.users_patcher = mock.patch.object(app, "users", self.users)
        self.users_patcher.start()
        self.client = app.app.test_client()

    def tearDown(self):
        self.users_patcher.stop()

    def test_login_success_sets_session_and_redirects_home(self):
        response = self.client.post(
            "/login", data={"email": "user@example.com", "password": "correct-password"}
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.headers["Location"], "/")
        with self.client.session_transaction() as sess:
            self.assertEqual(sess["user_email"], "user@example.com")

    def test_login_wrong_password_shows_error(self):
        response = self.client.post(
            "/login", data={"email": "user@example.com", "password": "wrong-password"}
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn("Invalid email or password", response.get_data(as_text=True))

    def test_login_unknown_email_shows_error(self):
        response = self.client.post(
            "/login", data={"email": "nobody@example.com", "password": "whatever1"}
        )
        self.assertIn("Invalid email or password", response.get_data(as_text=True))

    def test_login_redirects_to_safe_next(self):
        response = self.client.post(
            "/login",
            data={
                "email": "user@example.com",
                "password": "correct-password",
                "next": "/roasts",
            },
        )
        self.assertEqual(response.headers["Location"], "/roasts")

    def test_login_ignores_unsafe_next(self):
        response = self.client.post(
            "/login",
            data={
                "email": "user@example.com",
                "password": "correct-password",
                "next": "https://evil.example/",
            },
        )
        self.assertEqual(response.headers["Location"], "/")


class TestLogout(unittest.TestCase):
    def setUp(self):
        self.client = app.app.test_client()

    def test_logout_clears_session_and_redirects_home(self):
        login(self.client)
        response = self.client.post("/logout")
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.headers["Location"], "/")
        with self.client.session_transaction() as sess:
            self.assertNotIn("user_email", sess)


class TestLoginRequired(unittest.TestCase):
    def setUp(self):
        self.client = app.app.test_client()

    def test_gated_get_routes_redirect_to_login_when_logged_out(self):
        gated_get_routes = [
            "/roasts",
            "/roasts/some-id",
            "/roasts/new",
            "/roasts/new/some-profile",
            "/profiles",
            "/profiles/new",
            "/profiles/some-id",
            "/roasts/some-id/delete",
            "/profiles/some-id/delete",
        ]
        for path in gated_get_routes:
            with self.subTest(path=path):
                response = self.client.get(path)
                self.assertEqual(response.status_code, 302)
                self.assertTrue(response.headers["Location"].startswith("/login"))
                self.assertIn(path, response.headers["Location"])

    def test_gated_post_route_redirects_to_login_when_logged_out(self):
        response = self.client.post("/profiles/some-id/favorite")
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.headers["Location"].startswith("/login"))

    def test_home_stays_open_when_logged_out(self):
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)


class TestPerUserIsolation(unittest.TestCase):
    def setUp(self):
        self.records = {
            "record-a": {
                "date": "09/07/2026",
                "bean_name": "Owner A Roast",
                "green_weight": 200.0,
                "finished_weight": 170.0,
                "total_roast_time": 450,
                "time_of_first_crack": 375,
                "roast_profile_id": None,
                "target_temps": [None] * 12,
                "actual_temps": [None] * 12,
                "owner": "a@example.com",
            },
            "record-b": {
                "date": "09/07/2026",
                "bean_name": "Owner B Roast",
                "green_weight": 200.0,
                "finished_weight": 170.0,
                "total_roast_time": 450,
                "time_of_first_crack": 375,
                "roast_profile_id": None,
                "target_temps": [None] * 12,
                "actual_temps": [None] * 12,
                "owner": "b@example.com",
            },
        }
        self.profiles = {
            "profile-a": {"name": "Owner A Profile", "temps": [None] * 12, "owner": "a@example.com"},
            "profile-b": {"name": "Owner B Profile", "temps": [None] * 12, "owner": "b@example.com"},
        }
        self.records_patcher = mock.patch.object(app, "roast_records", self.records)
        self.profiles_patcher = mock.patch.object(app, "roast_profiles", self.profiles)
        self.records_patcher.start()
        self.profiles_patcher.start()
        self.client = app.app.test_client()

    def tearDown(self):
        self.records_patcher.stop()
        self.profiles_patcher.stop()

    def test_roasts_list_only_shows_current_users_records(self):
        login(self.client, "a@example.com")
        body = self.client.get("/roasts").get_data(as_text=True)
        self.assertIn("Owner A Roast", body)
        self.assertNotIn("Owner B Roast", body)

    def test_profiles_list_only_shows_current_users_profiles(self):
        login(self.client, "a@example.com")
        body = self.client.get("/profiles").get_data(as_text=True)
        self.assertIn("Owner A Profile", body)
        self.assertNotIn("Owner B Profile", body)

    def test_select_profile_only_shows_current_users_profiles(self):
        login(self.client, "a@example.com")
        body = self.client.get("/roasts/new").get_data(as_text=True)
        self.assertIn("Owner A Profile", body)
        self.assertNotIn("Owner B Profile", body)

    def test_cannot_view_another_users_roast_by_id(self):
        login(self.client, "a@example.com")
        response = self.client.get("/roasts/record-b")
        self.assertEqual(response.status_code, 404)

    def test_cannot_delete_another_users_roast_by_id(self):
        login(self.client, "a@example.com")
        response = self.client.get("/roasts/record-b/delete")
        self.assertEqual(response.status_code, 404)

    def test_cannot_view_another_users_profile_by_id(self):
        login(self.client, "a@example.com")
        response = self.client.get("/profiles/profile-b")
        self.assertEqual(response.status_code, 404)

    def test_cannot_delete_another_users_profile_by_id(self):
        login(self.client, "a@example.com")
        response = self.client.get("/profiles/profile-b/delete")
        self.assertEqual(response.status_code, 404)

    def test_cannot_select_another_users_profile_to_add_roast(self):
        login(self.client, "a@example.com")
        response = self.client.get("/roasts/new/profile-b")
        self.assertEqual(response.status_code, 404)

    def test_cannot_toggle_another_users_profile_favorite(self):
        login(self.client, "a@example.com")
        with mock.patch.object(app, "save_roast_profiles"):
            response = self.client.post("/profiles/profile-b/favorite")
        self.assertEqual(response.status_code, 404)


class TestVerifyEmail(unittest.TestCase):
    def setUp(self):
        self.users = {
            "user@example.com": {
                "password_hash": generate_password_hash("correct-password"),
                "created_at": "now",
                "email_verified": False,
                "verify_token": "good-token",
                "verify_token_expires": (
                    datetime.now() + timedelta(hours=1)
                ).isoformat(),
            }
        }
        self.users_patcher = mock.patch.object(app, "users", self.users)
        self.save_users_patcher = mock.patch.object(app, "save_users")
        self.users_patcher.start()
        self.save_users_patcher.start()
        self.client = app.app.test_client()

    def tearDown(self):
        self.users_patcher.stop()
        self.save_users_patcher.stop()

    def test_valid_token_verifies_account_and_clears_token(self):
        response = self.client.get("/verify-email/good-token")
        self.assertEqual(response.status_code, 200)
        self.assertIn("verified", response.get_data(as_text=True))
        user = self.users["user@example.com"]
        self.assertTrue(user["email_verified"])
        self.assertIsNone(user["verify_token"])
        self.assertIsNone(user["verify_token_expires"])
        app.save_users.assert_called_once_with(self.users)

    def test_expired_token_does_not_verify(self):
        self.users["user@example.com"]["verify_token_expires"] = (
            datetime.now() - timedelta(hours=1)
        ).isoformat()
        response = self.client.get("/verify-email/good-token")
        self.assertIn("invalid or has expired", response.get_data(as_text=True))
        self.assertFalse(self.users["user@example.com"]["email_verified"])

    def test_unknown_token_does_not_verify(self):
        response = self.client.get("/verify-email/no-such-token")
        self.assertIn("invalid or has expired", response.get_data(as_text=True))
        self.assertFalse(self.users["user@example.com"]["email_verified"])


class TestResendVerification(unittest.TestCase):
    def setUp(self):
        self.users = {
            "user@example.com": {
                "password_hash": generate_password_hash("correct-password"),
                "created_at": "now",
                "email_verified": False,
                "verify_token": "old-token",
                "verify_token_expires": (
                    datetime.now() + timedelta(hours=1)
                ).isoformat(),
            }
        }
        self.users_patcher = mock.patch.object(app, "users", self.users)
        self.save_users_patcher = mock.patch.object(app, "save_users")
        self.send_email_patcher = mock.patch.object(app, "send_email")
        self.users_patcher.start()
        self.save_users_patcher.start()
        self.send_email_patcher.start()
        self.client = app.app.test_client()

    def tearDown(self):
        self.users_patcher.stop()
        self.save_users_patcher.stop()
        self.send_email_patcher.stop()

    def test_requires_login(self):
        response = self.client.post("/resend-verification")
        self.assertEqual(response.status_code, 302)
        self.assertIn("/login", response.headers["Location"])
        app.send_email.assert_not_called()

    def test_regenerates_token_and_sends_email(self):
        login(self.client, "user@example.com")
        response = self.client.post("/resend-verification")
        self.assertEqual(response.status_code, 302)
        user = self.users["user@example.com"]
        self.assertNotEqual(user["verify_token"], "old-token")
        app.send_email.assert_called_once()
        to_address, subject, body = app.send_email.call_args[0]
        self.assertEqual(to_address, "user@example.com")
        self.assertIn(user["verify_token"], body)


class TestForgotPassword(unittest.TestCase):
    def setUp(self):
        self.users = {
            "user@example.com": {
                "password_hash": generate_password_hash("correct-password"),
                "created_at": "now",
                "reset_token": None,
                "reset_token_expires": None,
            }
        }
        self.users_patcher = mock.patch.object(app, "users", self.users)
        self.save_users_patcher = mock.patch.object(app, "save_users")
        self.send_email_patcher = mock.patch.object(app, "send_email")
        self.users_patcher.start()
        self.save_users_patcher.start()
        self.send_email_patcher.start()
        self.client = app.app.test_client()

    def tearDown(self):
        self.users_patcher.stop()
        self.save_users_patcher.stop()
        self.send_email_patcher.stop()

    def test_known_email_sets_token_and_sends_email(self):
        response = self.client.post(
            "/forgot-password", data={"email": "user@example.com"}
        )
        body = response.get_data(as_text=True)
        self.assertIn("we've sent a link", body)
        user = self.users["user@example.com"]
        self.assertTrue(user["reset_token"])
        app.send_email.assert_called_once()
        to_address, subject, sent_body = app.send_email.call_args[0]
        self.assertEqual(to_address, "user@example.com")
        self.assertIn(user["reset_token"], sent_body)

    def test_unknown_email_gives_identical_response_but_sends_nothing(self):
        response = self.client.post(
            "/forgot-password", data={"email": "nobody@example.com"}
        )
        body = response.get_data(as_text=True)
        self.assertIn("we've sent a link", body)
        app.send_email.assert_not_called()
        self.assertNotIn("nobody@example.com", self.users)

    def test_known_and_unknown_email_responses_are_identical(self):
        known_response = self.client.post(
            "/forgot-password", data={"email": "user@example.com"}
        ).get_data(as_text=True)
        app.send_email.reset_mock()
        unknown_response = self.client.post(
            "/forgot-password", data={"email": "nobody@example.com"}
        ).get_data(as_text=True)
        self.assertEqual(known_response, unknown_response)


class TestResetPassword(unittest.TestCase):
    def setUp(self):
        self.users = {
            "user@example.com": {
                "password_hash": generate_password_hash("old-password"),
                "created_at": "now",
                "reset_token": "good-token",
                "reset_token_expires": (
                    datetime.now() + timedelta(hours=1)
                ).isoformat(),
            }
        }
        self.users_patcher = mock.patch.object(app, "users", self.users)
        self.save_users_patcher = mock.patch.object(app, "save_users")
        self.users_patcher.start()
        self.save_users_patcher.start()
        self.client = app.app.test_client()

    def tearDown(self):
        self.users_patcher.stop()
        self.save_users_patcher.stop()

    def test_get_with_valid_token_shows_form(self):
        response = self.client.get("/reset-password/good-token")
        self.assertEqual(response.status_code, 200)
        self.assertIn("Set new password", response.get_data(as_text=True))

    def test_get_with_expired_token_shows_error(self):
        self.users["user@example.com"]["reset_token_expires"] = (
            datetime.now() - timedelta(hours=1)
        ).isoformat()
        response = self.client.get("/reset-password/good-token")
        self.assertIn("invalid or has expired", response.get_data(as_text=True))

    def test_get_with_unknown_token_shows_error(self):
        response = self.client.get("/reset-password/no-such-token")
        self.assertIn("invalid or has expired", response.get_data(as_text=True))

    def test_post_rejects_mismatched_confirmation(self):
        response = self.client.post(
            "/reset-password/good-token",
            data={"password": "longenough1", "confirm": "longenough2"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn("do not match", response.get_data(as_text=True))

    def test_post_rejects_short_password(self):
        response = self.client.post(
            "/reset-password/good-token",
            data={"password": "short1", "confirm": "short1"},
        )
        self.assertIn("at least 8 characters", response.get_data(as_text=True))

    def test_post_with_valid_token_sets_password_clears_token_and_logs_in(self):
        response = self.client.post(
            "/reset-password/good-token",
            data={"password": "longenough1", "confirm": "longenough1"},
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.headers["Location"], "/")
        user = self.users["user@example.com"]
        self.assertIsNone(user["reset_token"])
        self.assertIsNone(user["reset_token_expires"])
        with self.client.session_transaction() as sess:
            self.assertEqual(sess["user_email"], "user@example.com")

    def test_new_password_authenticates_and_old_password_no_longer_does(self):
        self.client.post(
            "/reset-password/good-token",
            data={"password": "longenough1", "confirm": "longenough1"},
        )
        user = self.users["user@example.com"]
        self.assertTrue(check_password_hash(user["password_hash"], "longenough1"))
        self.assertFalse(check_password_hash(user["password_hash"], "old-password"))

    def test_post_with_expired_token_shows_error_and_does_not_change_password(self):
        self.users["user@example.com"]["reset_token_expires"] = (
            datetime.now() - timedelta(hours=1)
        ).isoformat()
        response = self.client.post(
            "/reset-password/good-token",
            data={"password": "longenough1", "confirm": "longenough1"},
        )
        self.assertIn("invalid or has expired", response.get_data(as_text=True))
        user = self.users["user@example.com"]
        self.assertTrue(check_password_hash(user["password_hash"], "old-password"))


class TestAbout(unittest.TestCase):
    def setUp(self):
        self.send_email_patcher = mock.patch.object(app, "send_email")
        self.send_email_patcher.start()
        self.client = app.app.test_client()

    def tearDown(self):
        self.send_email_patcher.stop()

    def test_about_page_loads_without_login(self):
        response = self.client.get("/about")
        self.assertEqual(response.status_code, 200)
        self.assertIn("vibe-coding", response.get_data(as_text=True))

    def test_about_rejects_empty_message(self):
        response = self.client.post("/about", data={"message": "   "})
        self.assertEqual(response.status_code, 200)
        self.assertIn("Enter a message", response.get_data(as_text=True))
        app.send_email.assert_not_called()

    def test_about_sends_feedback_and_redirects(self):
        response = self.client.post(
            "/about", data={"message": "Love the app!", "reply_to": "fan@example.com"}
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.headers["Location"], "/about?sent=1")
        app.send_email.assert_called_once()
        to_address, subject, body = app.send_email.call_args[0]
        self.assertEqual(to_address, app.GMAIL_ADDRESS)
        self.assertIn("Crackle feedback", subject)
        self.assertIn("Love the app!", body)
        self.assertIn("fan@example.com", body)

    def test_about_shows_thank_you_after_sent(self):
        response = self.client.get("/about?sent=1")
        self.assertIn("on its way", response.get_data(as_text=True))


if __name__ == "__main__":
    unittest.main()
