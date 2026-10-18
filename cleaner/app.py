"""Flask REST API around the cleaning functions."""
import io

import pandas as pd
from flask import Flask, Response, jsonify, request

from .cleaning import clean, profile

MAX_UPLOAD_BYTES = 5 * 1024 * 1024


def create_app() -> Flask:
    app = Flask(__name__)
    app.config["MAX_CONTENT_LENGTH"] = MAX_UPLOAD_BYTES

    def read_upload() -> pd.DataFrame:
        file = request.files.get("file")
        if file is None or not file.filename:
            raise ValueError("Upload a CSV file in the 'file' form field.")
        try:
            return pd.read_csv(io.BytesIO(file.read()), dtype=str, encoding="utf-8-sig")
        except (pd.errors.ParserError, pd.errors.EmptyDataError, UnicodeDecodeError) as exc:
            raise ValueError(f"Could not read the CSV: {exc}") from exc

    @app.errorhandler(ValueError)
    def bad_request(exc):
        return jsonify(error=str(exc)), 400

    @app.errorhandler(413)
    def too_large(_):
        return jsonify(error="File too large (max 5 MB)."), 413

    @app.get("/health")
    def health():
        return jsonify(status="ok")

    @app.post("/api/profile")
    def api_profile():
        return jsonify(profile(read_upload()))

    @app.post("/api/clean")
    def api_clean():
        """Return the cleaned CSV. The report is sent in JSON when ?format=json."""
        df = read_upload()
        dates = tuple(c for c in request.args.get("date_columns", "").split(",") if c)
        cleaned, report = clean(
            df,
            phone_column=request.args.get("phone_column"),
            id_column=request.args.get("id_column"),
            date_columns=dates,
            drop_duplicates=request.args.get("drop_duplicates", "true").lower() != "false",
        )
        if request.args.get("format") == "json":
            return jsonify(report=report.as_dict(), rows=cleaned.fillna("").to_dict("records"))
        resp = Response(cleaned.to_csv(index=False), mimetype="text/csv")
        resp.headers["Content-Disposition"] = 'attachment; filename="cleaned.csv"'
        resp.headers["X-Rows-In"] = str(report.rows_in)
        resp.headers["X-Rows-Out"] = str(report.rows_out)
        return resp

    return app


if __name__ == "__main__":
    create_app().run(debug=True)
