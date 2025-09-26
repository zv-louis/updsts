# encoding: utf-8-sig

import sys
import os

def main():
    """Run pytest with optimal settings."""
    # Change to project root directory
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    os.chdir(project_root)
    
    try:
        import pytest
        
        # Basic pytest run
        args = [
            '-v',                           # Verbose output
            '--tb=short',                   # Short traceback format
            '--strict-markers',             # Strict marker handling
            'test/',                        # Test directory
        ]
        
        # Add coverage if available
        try:
            import pytest_cov
            args.extend([
                '--cov=src/updsts',
                '--cov-report=term-missing',
                '--cov-report=html:test/tmp/htmlcov',
                '--cov-report=xml:test/tmp/coverage.xml',
            ])
        except ImportError:
            print("pytest-cov not available, running without coverage")
        
        return pytest.main(args)
        
    except ImportError:
        print("pytest not available. Please install pytest:")
        print("  uv add --group test pytest pytest-cov pytest-mock")
        return 1

if __name__ == '__main__':
    sys.exit(main())