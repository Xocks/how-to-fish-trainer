import sys
import argparse

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

from .trainer import HowToFishTrainer


def main():
    parser = argparse.ArgumentParser(description="How to Fish - External Unity Mono Trainer")
    parser.add_argument(
        "--process",
        "-p",
        default="How to Fish.exe",
        help="Target process executable name (default: 'How to Fish.exe')",
    )
    parser.add_argument(
        "--lang",
        "-l",
        choices=["zh", "en"],
        default="en",
        help="Initial interface language: 'zh' (Chinese) or 'en' (English) (default: 'en')",
    )
    args = parser.parse_args()

    trainer = HowToFishTrainer(process_name=args.process, language=args.lang)
    try:
        trainer.run()
    except KeyboardInterrupt:
        trainer.stop()
        sys.exit(0)


if __name__ == "__main__":
    main()
