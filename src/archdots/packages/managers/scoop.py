import subprocess

from archdots.ui.console import err_console
from archdots.ui.progress import progress_decorator
from archdots.packages.managers.base import PackageManager
from archdots.packages.managers.custom import Custom
from archdots.utils.decorators import memoize


class Scoop(PackageManager):
    def __init__(self) -> None:
        super().__init__("scoop")

    @progress_decorator("scoop packages")
    @memoize
    def get_installed(self, use_memo=False, by_user=True) -> list[str]:
        import json

        def extract_json_payload(raw_output: str) -> str:
            raw_output = raw_output.strip()
            first_array = raw_output.find("[")
            first_obj = raw_output.find("{")

            starts = [idx for idx in (first_array, first_obj) if idx >= 0]
            if not starts:
                return ""
            return raw_output[min(starts) :]

        def normalize_results(scoop_result: object) -> list[dict[str, object]]:
            if isinstance(scoop_result, list):
                return [item for item in scoop_result if isinstance(item, dict)]
            if isinstance(scoop_result, dict):
                return [scoop_result]
            return []

        try:
            process = subprocess.run(
                ["powershell", "-Command", "scoop list | ConvertTo-Json -Depth 5"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                encoding="utf-8",
                timeout=30,
            )

            if process.returncode != 0 or not process.stdout.strip():
                return []

            json_payload = extract_json_payload(process.stdout)
            if not json_payload:
                return []

            scoop_result = json.loads(json_payload)
            results = normalize_results(scoop_result)
            pkg_names = [
                result["Name"]
                for result in results
                if "Name" in result and isinstance(result["Name"], str)
            ]
            custom_package_names = [pkg.name for pkg in Custom().get_packages(use_memo=use_memo)]
            return list(filter(lambda p: p not in custom_package_names, pkg_names))
        except json.JSONDecodeError:
            return []
        except subprocess.TimeoutExpired:
            err_console.print("[warning]scoop list command timed out[/warning]")
            return []
        except Exception as e:
            err_console.print(f"[warning]error running scoop list: {e}[/warning]")
            return []

    def install(self, packages: list[str], force=True) -> bool:
        if not packages:
            return True
        import subprocess

        # Ensure we know existing buckets to avoid slow add commands if already present
        installed_buckets = []
        try:
            buckets_output = subprocess.check_output(
                ["powershell", "-Command", "scoop bucket list | Select-Object -Skip 2 | % { ($_ -split ' +')[0] }"],
                text=True,
                encoding="utf-8",
                stderr=subprocess.DEVNULL
            )
            installed_buckets = [b.strip() for b in buckets_output.splitlines() if b.strip()]
        except Exception:
            pass # Fallback to trying to add anyway if detection fails

        error_happened = False
        for package in packages:
            if "/" in package:
                bucket_name, _ = package.split("/", 1)
                if bucket_name not in installed_buckets:
                    subprocess.run(f'scoop bucket add "{bucket_name}"', shell=True)
                    installed_buckets.append(bucket_name)

            error_happened = error_happened or subprocess.run(f'scoop install "{package}"', shell=True).returncode != 0
        return not error_happened

    def uninstall(self, packages: list[str]) -> bool:
        if not packages:
            return True
        import subprocess

        error_happened = False
        for package in packages:
            error_happened = error_happened or subprocess.run(f'scoop uninstall "{package}"', shell=True).returncode != 0
        return not error_happened

    def is_available(self) -> bool:
        from shutil import which

        return which("scoop") is not None
