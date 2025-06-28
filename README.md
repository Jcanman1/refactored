# refactored

OPC Dash Refactored

## Requirements

The application depends on the following Python packages:

- `dash`
- `dash-bootstrap-components`
- `python-opcua`
- `plotly`
- `pandas`
- `numpy`
- `python-i18n`

Dash Bootstrap Components is used throughout the dashboard layout, so be sure
it is available in your environment.

Install them with:

```bash
pip install -r requirements.txt
```

## Usage

Run the dashboard application:

```bash
python run_dashboard.py
```

To embed the layout in another Dash application, import `render_dashboard_shell`
from the `dashboard` package **and assign the return value to `app.layout`**.
This shell initializes the required `dcc.Store` components such as
`floors-data` and `machines-data`. Assigning `render_main_dashboard()` or
`render_new_dashboard()` to `app.layout` will mirror the legacy application's
behaviour and lead to "component not found" errors because these helpers return
only the inner grid without the prerequisite stores.

Example:

```python
from dash import Dash
from dashboard.layout import render_dashboard_shell

app = Dash(__name__)
app.layout = render_dashboard_shell()
```

Images used by the dashboard should be placed in an `assets/` directory that
resides next to the script so Dash can serve them automatically.
The provided `EnpresorMachine.png` image is included in this `assets/` folder.

Metrics and control logs written by the dashboard are automatically saved
to an `exports/` directory. This folder will be created at runtime if it does
not already exist.

The `Audiowide-Regular.ttf` font used when generating PDF reports is kept in
the repository root. Ensure this file remains in place so the report generator
can locate it.

## Package layout

The project is structured as a Python package named `dashboard`:

- `dashboard/__init__.py` exposes the main Dash `app` and re-exports helpers.
- `dashboard/callbacks.py` loads all callback definitions.
- `dashboard/layout.py` provides layout building utilities.
- `dashboard/opc_client.py` contains OPC UA connection helpers.
- `dashboard/settings.py` handles user configuration and unit conversions.
- `dashboard/state.py` defines the global state classes used by the app.

Use `python run_dashboard.py` to start the application which uses this package.


## Legacy Compatibility

This project aims to reproduce the features and appearance of the original dashboard implemented in `EnpresorOPCDataViewBeforeRestructureLegacy.py`.
Run the legacy script to compare behaviours and layout:

```bash
python EnpresorOPCDataViewBeforeRestructureLegacy.py
```

Refer to this file whenever implementing or modifying functionality to ensure the modern code stays aligned with the legacy version.

The new dashboard replicates all legacy settings features including theme selection, capacity units, language options, IP address management and SMTP email configuration.
