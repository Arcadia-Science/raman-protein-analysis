# SEC Plot — Web GUI

## 1. Install dependencies & start the server

From the `SEC Plotting Tool` folder:

```bash
cd "<path-to-folder>/SEC Plotting Tool"
pip install -r requirements.txt
python3 app.py
```

You should see:

- `Running on http://127.0.0.1:5000`
- Leave this terminal open while you use the GUI.

## 2. Open the GUI

In your browser go to:

**http://127.0.0.1:5000**

## 3. Use the GUI

1. **Upload CSV** — Choose a CSV with the same layout as the Data sheet (pairs of Volume, signal columns; first row = headers).
2. **Confirm mapping** — Check or edit the series names and plot title.
3. **Generate SVG** — Click the button; the plot appears below with a **Download SVG** link.

To stop the server, press **Ctrl+C** in the terminal.
