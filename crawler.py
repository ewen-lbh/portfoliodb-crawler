from pathlib import Path
from typing import Any
import re
from shutil import copy2, rmtree
import sys
from subprocess import run

def p(indent_level: int, *args: Any, **kwargs: Any):
    args = list(args)
    if indent_level == 0:
        args = ['\n'] + args
    print(indent_level * "  ", *args, **kwargs)

source_pattern = re.compile(r'[>!]\[[^\]]*\]\(([^\)]+)\)')
target_database = (Path.cwd() / sys.argv[1]).resolve()

p(0, f"Target database is {target_database}")
p(0, "Gathering all files for database compilation:")

def crawl(directory: Path, recurse = True):
    for project in directory.iterdir():
        if not project.is_dir() or project.name.startswith('.'):
            continue

        if not (project / ".portfoliodb").exists():
            continue

        if not (project / ".portfoliodb" / "description.md").exists():
            continue
        
        if project.name == "music":
            crawl(project, recurse=False)

        p(1, f"Crawling {project.name}...")
        description = (project / ".portfoliodb" / "description.md").read_text()

        (target_database/project.name).mkdir(exist_ok=True, parents=True)

        if (matches := source_pattern.finditer(description)):
            for match in matches:
                if match.group(1).startswith(('https:', 'http:', 'mailto:')):
                    continue
                source = Path(match.group(1))
                if not source.is_absolute():
                    source = (project / ".portfoliodb" / source).resolve()
                p(2, f"Found reference to file {source}")
                destination = target_database / project.name / source.name
                p(3, f"Copying to {destination}...")
                copy2(source, destination)
                p(2, f"Adjusting the path in the description file...")
                description = description.replace(match.group(1), str(destination))

        p(2, f"Writing the description file...")
        with open(target_database/project.name/"description.md", "w", encoding="utf-8") as file:
            file.write(description)

crawl(Path.home() / "projects")

if '--build' in sys.argv:

    p(0, "Building database:")
    p(1, f"$ portfoliodb {target_database} build database.json")

    run(["portfoliodb", target_database, "build", "database.json", "--silent"])

    if '--cleanup' in sys.argv:
        p(0, "Cleaning up...")
        p(1, f"Deleting {target_database}")
        rmtree(target_database)
