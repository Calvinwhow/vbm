#!/usr/bin/env python3
"""Identify sessions and optionally reorganize segmentation outputs into session/anat."""
from __future__ import annotations

import argparse
from pathlib import Path
import shutil


def list_sessions(base_dir: Path) -> dict[str, list[str]]:
    subjects = sorted(p for p in base_dir.glob("sub-*") if p.is_dir())
    sessions: dict[str, list[str]] = {}
    for subj in subjects:
        subj_sessions = sorted(p.name for p in subj.glob("ses-*") if p.is_dir())
        sessions[subj.name] = subj_sessions
        if subj_sessions:
            print(f"{subj.name}: {', '.join(subj_sessions)}")
        else:
            print(f"{subj.name}: no session folders")
    return sessions


def move_dir_contents(src: Path, dest: Path) -> None:
    if not src.exists() or not src.is_dir():
        return
    contents = list(src.iterdir())
    if not contents:
        return
    dest.mkdir(parents=True, exist_ok=True)
    for item in contents:
        target = dest / item.name
        if target.exists():
            print(f"Skipping move (exists): {target}")
            continue
        print(f"Moving {item} -> {target}")
        shutil.move(str(item), str(target))
    try:
        src.rmdir()
    except OSError:
        pass


def organize_outputs(base_dir: Path, session: str, dry_run=True) -> None:
    if dry_run:
        print("organize_sessions.organize_outputs(dry_run=True). Not forcing organization.")
        return
    subjects = sorted(p for p in base_dir.glob("sub-*") if p.is_dir())
    for subj in subjects:
        session_dirs = sorted(p for p in subj.glob("ses-*") if p.is_dir())
        if session_dirs:
            for ses_dir in session_dirs:
                anat_dir = ses_dir / "anat"
                for folder in ("mri", "report", "err"):
                    move_dir_contents(ses_dir / folder, anat_dir / folder)
        else:
            ses_dir = subj / session
            anat_dir = ses_dir / "anat"
            for folder in ("mri", "report", "err"):
                move_dir_contents(subj / folder, anat_dir / folder)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="List sessions under each subject and optionally organize segmentation outputs."
    )
    parser.add_argument("--base-dir", type=Path, required=True, help="Root data directory (e.g., /root/data).")
    parser.add_argument("--session", type=str, default="ses-01", help="Session name to use when creating folders.")
    parser.add_argument("--organize", action="store_true", help="Move segmentation outputs into <subject>/<session>/anat/ folders.")
    return parser


def main() -> None:
    args = build_parser().parse_args()
    if not args.base_dir.exists():
        raise SystemExit(f"Base directory not found: {args.base_dir}")
    list_sessions(args.base_dir)
    if args.organize:
        organize_outputs(args.base_dir, args.session)


if __name__ == "__main__":
    main()
