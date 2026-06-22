import unittest
import sys
import time
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


class ColoredTestResult(unittest.TextTestResult):

    GREEN = "\033[92m"
    RED = "\033[91m"
    YELLOW = "\033[93m"
    CYAN = "\033[96m"
    BOLD = "\033[1m"
    RESET = "\033[0m"

    def __init__(self, stream, descriptions, verbosity):
        super().__init__(stream, descriptions, verbosity)
        self.successes_count = 0

    def addSuccess(self, test):
        super().addSuccess(test)
        self.successes_count += 1
        self.stream.write(f"  {self.GREEN}✓{self.RESET} {test}\n")

    def addFailure(self, test, err):
        super().addFailure(test, err)
        self.stream.write(f"  {self.RED}✗ FAIL{self.RESET} {test}\n")
        self.stream.write(f"    {self.RED}{err[1]}{self.RESET}\n")

    def addError(self, test, err):
        super().addError(test, err)
        self.stream.write(f"  {self.RED}✗ ERROR{self.RESET} {test}\n")
        self.stream.write(f"    {self.RED}{err[1]}{self.RESET}\n")


class ColoredTestRunner(unittest.TextTestRunner):

    resultclass = ColoredTestResult

    def run(self, test):
        C = ColoredTestResult

        self.stream.write(f"\n{C.BOLD}{C.CYAN}{'='*60}{C.RESET}\n")
        self.stream.write(f"{C.BOLD}  ⚡ EsportsHub — Test Suite{C.RESET}\n")
        self.stream.write(f"{C.CYAN}{'='*60}{C.RESET}\n\n")

        start = time.time()
        result = super().run(test)
        elapsed = time.time() - start

        total = result.successes_count + len(result.failures) + len(result.errors)
        passed = result.successes_count
        failed = len(result.failures)
        errors = len(result.errors)

        self.stream.write(f"\n{C.CYAN}{'─'*60}{C.RESET}\n")
        self.stream.write(f"{C.BOLD}  Summary:{C.RESET}\n")
        self.stream.write(f"    Total:   {total}\n")
        self.stream.write(f"    {C.GREEN}Passed:  {passed}{C.RESET}\n")

        if failed > 0:
            self.stream.write(f"    {C.RED}Failed:  {failed}{C.RESET}\n")
        if errors > 0:
            self.stream.write(f"    {C.RED}Errors:  {errors}{C.RESET}\n")

        self.stream.write(f"    Time:    {elapsed:.2f}s\n")

        if failed + errors == 0:
            self.stream.write(f"\n  {C.GREEN}{C.BOLD}✓ ALL TESTS PASSED{C.RESET}\n")
        else:
            self.stream.write(f"\n  {C.RED}{C.BOLD}✗ SOME TESTS FAILED{C.RESET}\n")

        self.stream.write(f"{C.CYAN}{'='*60}{C.RESET}\n\n")

        return result


def main():
    loader = unittest.TestLoader()
    project_dir = os.path.dirname(os.path.abspath(__file__))
    suite = loader.discover(
        os.path.join(project_dir, "tests"),
        pattern="test_*.py",
        top_level_dir=project_dir,
    )

    runner = ColoredTestRunner(verbosity=0)
    result = runner.run(suite)

    sys.exit(0 if result.wasSuccessful() else 1)


if __name__ == "__main__":
    main()
