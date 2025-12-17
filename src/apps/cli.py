import argparse
from rich import print

from src.core.orchestrator import Orchestrator


def main():
    parser = argparse.ArgumentParser(
        description="Agent Forge - main agent CLI"
    )
    parser.add_argument(
        "--mode",
        choices=["file", "project", "meta-project"],
        default="file",
        help=(
            "Operation mode: "
            "'file' for single-file, "
            "'project' for multi-file planning, "
            "'meta-project' for triad-based meta planning and build."
        ),
    )
    parser.add_argument(
        "--edit",
        action="store_true",
        help="(file mode) Edit an existing file instead of generating from scratch.",
    )
    parser.add_argument(
        "--run-tests",
        action="store_true",
        help="(project/meta-project mode) After planning and generating, run pytest for the project.",
    )
    parser.add_argument(
        "--file",
        help="Target file path to generate/edit (file mode), e.g. src/app/main.py",
    )
    parser.add_argument(
        "--project-root",
        help="Project root directory (relative) for project/meta-project mode, e.g. src/my_app",
    )
    parser.add_argument(
        "--desc",
        required=True,
        help="Natural language description of what to build or edit.",
    )
    parser.add_argument(
        "--workspace",
        default=".",
        help="Workspace directory (default: current dir).",
    )
    parser.add_argument(
        "--triad",
        action="store_true",
        help="(file mode) Use three engineering personas and a chief to generate the file.",
    )
    parser.add_argument(
        "--run",
        action="store_true",
        help="(file mode only) After generating, run the script and show output.",
    )

    args = parser.parse_args()

    orch = Orchestrator(workspace_dir=args.workspace)

    # ---------------- META-PROJECT MODE ----------------
    if args.mode == "meta-project":
        if not args.project_root:
            raise SystemExit(
                "--project-root is required when --mode meta-project is used."
            )

        result = orch.meta_build_project(
            project_root=args.project_root,
            goal=args.desc,
        )

        print("[bold magenta]Meta-project planning and generation complete![/bold magenta]")
        print(f"[cyan]Project Task ID:[/cyan] {result['project_task_id']}")
        print(f"[cyan]Project root:[/cyan] {result['project_root']}")
        print(
            "[cyan]Meta-plan summary:[/cyan] "
            f"{result['meta_plan'].get('project', {}).get('summary', '')}"
        )
        print(f"[cyan]Number of files:[/cyan] {len(result['file_results'])}")

        print("[cyan]Files generated:[/cyan]")
        for fr in result["file_results"]:
            print(f" - {fr['file_path']} (task {fr.get('task_id', '?')})")

        if args.run_tests:
            test_result = orch.run_project_tests(args.project_root)
            tr = test_result["result"]
            print("\n[bold yellow]Test run (pytest) results:[/bold yellow]")
            print(f"[cyan]Workdir:[/cyan] {tr['workdir']}")
            print(f"[cyan]Command:[/cyan] {' '.join(tr['cmd'])}")
            print(f"[cyan]Exit code:[/cyan] {tr['exit_code']}")
            print("[cyan]STDOUT:[/cyan]")
            print(tr["stdout"] or "(no stdout)")
            print("[cyan]STDERR:[/cyan]")
            print(tr["stderr"] or "(no stderr)")

        return

    # ---------------- PROJECT MODE ----------------
    if args.mode == "project":
        if not args.project_root:
            raise SystemExit(
                "--project-root is required when --mode project is used."
            )

        result = orch.plan_and_build_project(
            project_root=args.project_root,
            goal=args.desc,
        )

        print("[bold green]Project planning and generation complete![/bold green]")
        print(f"[cyan]Project Task ID:[/cyan] {result['project_task_id']}")
        print(f"[cyan]Project root:[/cyan] {result['project_root']}")
        print(f"[cyan]Plan summary:[/cyan] {result['plan'].get('summary', '')}")
        print(f"[cyan]Number of files:[/cyan] {len(result['file_results'])}")

        print("[cyan]Files generated:[/cyan]")
        for fr in result["file_results"]:
            print(f" - {fr['file_path']} (task {fr.get('task_id', '?')})")

        if args.run_tests:
            test_result = orch.run_project_tests(args.project_root)
            tr = test_result["result"]
            print("\n[bold yellow]Test run (pytest) results:[/bold yellow]")
            print(f"[cyan]Workdir:[/cyan] {tr['workdir']}")
            print(f"[cyan]Command:[/cyan] {' '.join(tr['cmd'])}")
            print(f"[cyan]Exit code:[/cyan] {tr['exit_code']}")
            print("[cyan]STDOUT:[/cyan]")
            print(tr["stdout"] or "(no stdout)")
            print("[cyan]STDERR:[/cyan]")
            print(tr["stderr"] or "(no stderr)")

        return

    # ---------------- FILE MODE ----------------
    if not args.file:
        raise SystemExit(
            "--file is required when --mode file (default) is used."
        )

    if args.edit and args.triad:
        raise SystemExit("--edit and --triad cannot be used together in file mode.")

    if args.edit and args.run:
        raise SystemExit("--edit and --run together are not supported yet; run the script manually after editing.")

    # 1) Triad mode: three personas + chief engineer decide the file
    if args.triad:
        result = orch.triad_generate_file(
            file_path=args.file,
            description=args.desc,
        )

        print("[bold green]Triad file generation complete![/bold green]")
        print(f"[cyan]Task ID:[/cyan] {result['task_id']}")
        print(f"[cyan]Path:[/cyan] {result['file_path']}")

        print("[cyan]Candidate previews:[/cyan]")
        for c in result["candidates"]:
            preview_repr = repr(c["preview"])
            print(f" - {c['label']} ({c['name']}): {preview_repr}")

        print("\n[cyan]Final preview:[/cyan]")
        print(result["final_preview"])
        return

    # 2) Run mode: generate and run a single file (no edit)
    if args.run:
        result = orch.generate_and_run(
            file_path=args.file,
            description=args.desc,
        )

        print("[bold green]File generation and run complete![/bold green]")
        print(f"[cyan]Task ID:[/cyan] {result['task_id']}")
        print(f"[cyan]Path:[/cyan] {result['file_path']}")
        print(f"[cyan]Final exit code:[/cyan] {result['final_exit_code']}")

        if result["runs"]:
            last_run = result["runs"][-1]
            print("[cyan]Last run command:[/cyan]", " ".join(map(str, last_run["cmd"])))
            print("[cyan]Last run stdout:[/cyan]")
            print(last_run["stdout"] or "(no stdout)")
            print("[cyan]Last run stderr:[/cyan]")
            print(last_run["stderr"] or "(no stderr)")

        return

    # 3) Edit mode: edit an existing file using the orchestrator
    if args.edit:
        result = orch.edit_file(
            file_path=args.file,
            description=args.desc,
        )

        print("[bold green]File edit complete![/bold green]")
        print(f"[cyan]Path:[/cyan] {result['file_path']}")
        if "tool_result" in result:
            print(f"[cyan]Tool result:[/cyan] {result['tool_result']}")
        print("[cyan]Preview:[/cyan]")
        print(result.get("preview", ""))

        return

    # 4) Simple file generation (default file mode)
    result = orch.generate_file(
        file_path=args.file,
        description=args.desc,
    )

    print("[bold green]File generation complete![/bold green]")
    if "task_id" in result:
        print(f"[cyan]Task ID:[/cyan] {result['task_id']}")
    print(f"[cyan]Path:[/cyan] {result['file_path']}")
    if "tool_result" in result:
        print(f"[cyan]Tool result:[/cyan] {result['tool_result']}")
    print("[cyan]Preview:[/cyan]")
    print(result.get("preview", ""))


if __name__ == "__main__":
    main()
