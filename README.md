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

Install them with:

```bash
pip install -r requirements.txt
```

## Usage

Run the dashboard application:

```bash
python EnpresorOPCDataViewBeforeRestructure.py
```

Alternatively you can start the same dashboard with `python run_dashboard.py`.

Images used by the dashboard should be placed in an `assets/` directory that
resides next to the script so Dash can serve them automatically.
The provided `EnpresorMachine.png` image is included in this `assets/` folder.

