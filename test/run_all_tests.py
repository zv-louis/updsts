# encoding: utf-8-sig

import sys
import os

def main():
    """Run all tests with pytest and coverage reporting."""
    # Change to project root directory
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    os.chdir(project_root)
    
    try:
        import pytest
        # Run pytest with comprehensive coverage
        args = [
            '--cov=src/updsts',
            '--cov-report=html:test/tmp/htmlcov',
            '--cov-report=term-missing',
            '--cov-report=xml:test/tmp/coverage.xml',
            '--cov-branch',
            '-v',
            '--tb=short',
            '--strict-markers',
            'test/'
        ]
        
        return pytest.main(args)
        
    except ImportError:
        print("Error: pytest not available. Please install pytest:")
        print("  uv add --group test pytest pytest-cov pytest-mock")
        return 1

if __name__ == '__main__':
    sys.exit(main())