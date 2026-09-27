"""Template for your own plugin. Copy to ~/.clockbind/plugins/ (or a folder listed in
CLOCKBIND_PLUGINS) and it appears as:  clockbind hello run --data file.csv"""
from clockbind.core.io import load_data, write_tables
from clockbind.core.plugin import Plugin
from clockbind.core.provenance import RunLog


def run(a):
    df = load_data(a.data)
    with RunLog(a.out, "hello", "run", vars(a), None) as log:   # always use RunLog
        log.add_input(a.data)
        write_tables(log, {"rows": df.head()}, "hello")


class Hello(Plugin):
    name = "hello"
    help = "Example plugin"

    def register(self, sub):
        p = sub.add_parser("run", help="Show the first rows")
        p.add_argument("--data", required=True)
        p.add_argument("--out", default="clockbind_runs")
        p.set_defaults(func=run)


PLUGIN = Hello()
