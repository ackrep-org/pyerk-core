import datetime
from jinja2 import Environment, PackageLoader, select_autoescape, FileSystemLoader
from ipydex import IPS
import addict

from . import erkloader

try:
    # this will be part of standard library for python >= 3.11
    import tomllib
except ModuleNotFoundError:
    import tomli as tomllib

from . import settings


def generate_report(reportconf_path: str):

    reportconf = load_report_conf(reportconf_path)
    mods = load_modules(reportconf)
    # IPS()

    jin_env = Environment(loader=FileSystemLoader(settings.TEMPLATE_PATH))
    template_doc = jin_env.get_template('report-template.tex')

    context = {
        "date": datetime.datetime.today().strftime(r"%Y-%m-%d"),
        "nodes": 10,
        "edges": 22,
    }
    res = template_doc.render(c=context)
    # IPS()

    fname = "report.tex"
    with open(fname, "w") as resfile:
        resfile.write(res)
    print(fname, "written.")


def load_modules(reportconf: dict) -> list:

    res = []
    if not (lmdict := reportconf.get("load_modules")):
        return res

    assert isinstance(lmdict, dict)

    for prefix, path in lmdict.items():
        mod = erkloader.load_mod_from_path(path, prefix=prefix)
        res.append(mod)

    return res


def load_report_conf(reportconf_path: str) -> addict.Addict:
    """

    """

    try:
        with open(reportconf_path, "rb") as fp:
            conf = tomllib.load(fp)
    except FileNotFoundError:
        raise

    return conf
