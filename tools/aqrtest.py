#!/usr/bin/env python3
# project aquarium's testing battery
# Copyright (C) 2021 SUSE, LLC.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

import sys
import errno
from pathlib import Path
from libaqr.errors import BoxAlreadyExistsError, ImageNotFoundError, VagrantError
from libaqr.images import Image
from libaqr.runner import Runner, RunnerResult
from libaqr.suites import (
    SuiteEntry,
    get_available_suites,
    get_suite_tests
)
from libaqr.misc import find_builds_path
from typing import List, Optional, Tuple
import click


@click.group()
def app() -> None:
    pass


@app.command("run")
@click.argument("image", required=True, type=str)
@click.option("-t", "--test", required=False, type=str)
@click.option("-s", "--suite", required=False, type=str)
@click.option("--suites-path", required=False, type=Path)
def cmd_run(
    image: str,
    test: Optional[str],
    suite: Optional[str],
    suites_path: Optional[Path]
) -> None:
    """ Run a test or a suite against a given image """

    suitesdir = suites_path if suites_path else Path("tests/suites")

    if not suitesdir.exists():
        click.secho("error: unable to find suites directory", fg="red")
        sys.exit(errno.ENOENT)

    available_suites = get_available_suites(suitesdir)
    if suite:
        if suite not in available_suites:
            click.secho(f"error: unknown suite '{suite}'", fg="red")
            sys.exit(errno.EINVAL)
        available_suites = [suite]

    if len(available_suites) == 0:
        click.secho("No suites found", fg="yellow")
        sys.exit(0)

    # add suites parent directory to pythonpath so we can import modules
    sys.path.append(suitesdir.parent.as_posix())

    # prepare image
    try:
        Image.add(find_builds_path(), image)
    except ImageNotFoundError as e:
        click.secho(
            f"error: unable to find image '{image}': {e.message}",
            fg="red"
        )
        sys.exit(e.errno)
    except VagrantError as e:
        click.secho(f"error: {e.message}", fg="red")
        sys.exit(e.errno)
    except BoxAlreadyExistsError:
        # we are going to reuse that box
        pass

    deployments_path = Path("aqrtest-deployments")
    deployments_path.mkdir(exist_ok=True)

    has_failures = False
    results: List[Tuple[SuiteEntry, RunnerResult]] = []
    for entry in get_suite_tests(suitesdir, suite, test):
        runner = Runner(deployments_path, image, entry)
        runner.start()
        result = runner.result
        runner.join()
        results.append((entry, result))
        if result.retcode != 0:
            has_failures = True

    for suite_entry, result in results:
        print(f"--- Suite: {suite_entry.name}")
        print(f"   Result: {result.retcode} ({len(result.cases)} cases)")
        for casename, res in result.cases.items():
            print(f"   * {casename}")
            for n, r in res.results:
                print(f"   `- {n}: {r}")
            print(f"   '- Total: {len(res.failures)} failures")

    if has_failures:
        sys.exit(1)
    sys.exit(0)


@app.command("daemon")
@click.argument("id", required=True, type=str)
def cmd_daemon(id: str) -> None:
    """ Run inside the VM, runs aquarium """
    pass


@app.command("list")
@click.option("--suites-path", required=False, type=Path)
def cmd_list(suites_path: Optional[Path]) -> None:
    """ List available suites """

    suitesdir = suites_path if suites_path else Path("tests/suites")
    if not suitesdir.exists():
        click.secho("No suites found", bold=True)
        return

    available_suites = get_available_suites(suitesdir)
    for suite_name in available_suites:
        for entry in get_suite_tests(suitesdir, suite_name, None):
            click.secho("{} {}/{}".format(
                click.style(chr(0x25cf), fg="cyan", bold=True),
                suite_name, entry.name
            ))


if __name__ == "__main__":
    app()
