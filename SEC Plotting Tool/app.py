#!/usr/bin/env python3
"""
Flask backend for SEC plot web GUI. Serves the HTML UI and /api/plot for CSV -> SVG.
Run: python app.py  then open http://127.0.0.1:5000
"""

import io
import sys
import traceback
from pathlib import Path

import pandas as pd
from flask import Flask, jsonify, request, send_from_directory

# Ensure we can import plot_sec_to_svg from the same directory
_SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(_SCRIPT_DIR))

from plot_sec_to_svg import pairs_from_mapping, render_sec_svg, suggest_legend

app = Flask(__name__, static_folder=str(_SCRIPT_DIR / "static"))


@app.route("/")
def index():
    return send_from_directory(_SCRIPT_DIR, "sec_plot_gui.html")


@app.route("/api/suggest-labels", methods=["POST"])
def api_suggest_labels():
    """Expects JSON: { csv_text, series }. Returns legend_title and labels as they would appear on the figure."""
    try:
        data = request.get_json(force=True, silent=False)
    except Exception as e:
        return jsonify({"error": f"Invalid JSON: {e}"}), 400
    if not data:
        return jsonify({"error": "No JSON body"}), 400
    try:
        csv_text = data.get("csv_text", "").strip()
        series = data.get("series", [])
        if not csv_text or not series:
            return jsonify({"error": "csv_text and series required"}), 400
        df = pd.read_csv(io.StringIO(csv_text), header=0)
        pairs = pairs_from_mapping(df, series)
        if not pairs:
            return jsonify({"error": "No valid data from the given column mapping"}), 400
        legend_title, labels = suggest_legend(pairs)
        return jsonify({"legend_title": legend_title, "labels": labels})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/plot", methods=["POST"])
def api_plot():
    """Expects JSON: { csv_text, series, title, legend_title?, legend_labels? }. Returns SVG string."""
    try:
        data = request.get_json(force=True, silent=False)
    except Exception as e:
        return jsonify({"error": f"Invalid JSON: {e}"}), 400
    if not data:
        return jsonify({"error": "No JSON body"}), 400
    try:
        csv_text = data.get("csv_text", "").strip()
        series = data.get("series", [])
        title = (data.get("title") or "SEC Plot").strip() or "SEC Plot"
        legend_title = data.get("legend_title") or None
        legend_labels = data.get("legend_labels") or None
        if not csv_text:
            return jsonify({"error": "csv_text is required"}), 400
        if not series:
            return jsonify({"error": "At least one series (x_col, y_col, name) is required"}), 400
        df = pd.read_csv(io.StringIO(csv_text), header=0)
        pairs = pairs_from_mapping(df, series)
        if not pairs:
            return jsonify({"error": "No valid data from the given column mapping"}), 400
        svg = render_sec_svg(pairs, title, legend_title=legend_title, legend_labels=legend_labels)
        return jsonify({"svg": svg})
    except Exception as e:
        tb = traceback.format_exc()
        return jsonify({"error": str(e), "detail": tb}), 500


if __name__ == "__main__":
    import os
    host = "0.0.0.0" if os.environ.get("PORT") else "127.0.0.1"
    port = int(os.environ.get("PORT", 5000))
    app.run(host=host, port=port, debug=not os.environ.get("PORT"))
