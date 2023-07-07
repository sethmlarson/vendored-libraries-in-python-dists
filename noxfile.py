import nox

source_files = ("scripts/", "noxfile.py")


@nox.session()
def format(session):
    session.install("black", "isort")
    session.run("black", *source_files)
    session.run("isort", "--profile=black", *source_files)
