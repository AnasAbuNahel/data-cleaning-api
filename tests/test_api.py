import io
import unittest

from cleaner.app import create_app

CSV = (
    "id,name,phone,joined\n"
    "123456789,  Sara   Ahmad ,059 765-4321,31/12/2025\n"
    "123456789,Sara Ahmad,0597654321,31/12/2025\n"
    "12345,Ali,123,2026-01-05\n"
)


class ApiTests(unittest.TestCase):
    def setUp(self):
        self.client = create_app().test_client()

    def upload(self, url, text=CSV, name="data.csv"):
        return self.client.post(
            url,
            data={"file": (io.BytesIO(text.encode("utf-8")), name)},
            content_type="multipart/form-data",
        )

    def test_health(self):
        self.assertEqual(self.client.get("/health").get_json(), {"status": "ok"})

    def test_profile(self):
        r = self.upload("/api/profile")
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.get_json()["rows"], 3)

    def test_clean_returns_csv_with_headers(self):
        r = self.upload("/api/clean?phone_column=phone&date_columns=joined")
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.mimetype, "text/csv")
        self.assertEqual((r.headers["X-Rows-In"], r.headers["X-Rows-Out"]), ("3", "2"))
        self.assertIn("0597654321", r.get_data(as_text=True))
        self.assertIn("2025-12-31", r.get_data(as_text=True))

    def test_clean_json_report(self):
        r = self.upload("/api/clean?format=json&phone_column=phone&id_column=id")
        body = r.get_json()
        self.assertEqual(body["report"]["duplicates_removed"], 1)
        self.assertEqual(body["report"]["invalid_phones"], 1)
        self.assertEqual(body["report"]["invalid_ids"], 1)

    def test_missing_file_is_a_400(self):
        r = self.client.post("/api/profile")
        self.assertEqual(r.status_code, 400)
        self.assertIn("error", r.get_json())

    def test_empty_csv_is_a_400(self):
        r = self.upload("/api/profile", text="")
        self.assertEqual(r.status_code, 400)


if __name__ == "__main__":
    unittest.main()
