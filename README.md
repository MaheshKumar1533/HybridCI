# HybridCI - Intelligent Build Optimization System

A sophisticated CI/CD optimization engine that uses **Intelligent Build Selection Trees (IBST)** and **Language-Aware Caching** to dramatically reduce build times by selecting only the tests affected by code changes.

## Features

### 🚀 Core Capabilities

- **Intelligent Test Selection**: Analyzes code changes to identify only affected tests
- **Hybrid Execution Mode**: Combines baseline and optimized test selection strategies
- **Language-Aware Caching**: Maintains separate caches per programming language for optimal hit rates
- **Dependency Graph Analysis**: Tracks file-to-test mappings and dependencies
- **Change Detection**: Uses git to identify what's changed between commits
- **Real-time Dashboard**: Modern web interface with performance metrics and analytics

### 🎯 Test Optimization

- **Smart Filtering**: Select tests based on actual code changes
- **Baseline Mode**: Run all tests for reference and validation
- **Cache Management**: Avoid re-running unchanged code paths
- **Multi-Language Support**: Optimizations work across 15+ programming languages

### 📊 Analytics & Monitoring

- **Performance Metrics**: Track CI execution time trends
- **Cache Hit Rate**: Monitor cache effectiveness
- **Language Distribution**: View language composition of your project
- **Run History**: Detailed logs of all CI executions with language information
- **Language-Specific Stats**: Cache breakdown by programming language

## Project Structure

```
HybridCI/
├── ci_engine/                      # Core CI optimization engine
│   ├── __init__.py
│   ├── cache_manager.py           # Cache storage (language-aware)
│   ├── change_detector.py         # Git-based change detection
│   ├── dependency_graph.py        # Dependency analysis
│   ├── ibst.py                    # Intelligent Build Selection
│   ├── pipeline_runner.py         # Main execution pipeline
│   ├── test_mapper.py             # Test-to-source mapping
│   ├── language_utils.py          # Language utilities (NEW)
│   └── test_language_aware.py     # Language caching tests (NEW)
├── dashboard/                      # Flask-based web dashboard
│   ├── app.py                     # Flask application
│   ├── models.py                  # Database models
│   ├── static/
│   │   ├── styles.css             # Modern responsive styling
│   │   └── charts.js              # Chart utilities
│   └── templates/
│       ├── index.html             # Main dashboard
│       ├── runs.html              # Run history
│       └── cache_stats.html       # Cache statistics (NEW)
├── docker/
│   └── Dockerfile                 # Container configuration
├── experiments/
│   └── run_experiment.py          # Experimental scripts
├── sample_repo/                   # Example project for testing
│   ├── src/
│   │   ├── auth.py
│   │   ├── calculator.py
│   │   └── utils.py
│   └── tests/
│       ├── test_auth.py
│       ├── test_calculator.py
│       └── test_utils.py
├── LANGUAGE_AWARE_CACHING.md      # Language-aware feature guide
└── README.md                      # This file
```

## Quick Start

### Prerequisites

- Python 3.8+
- Git
- pip or conda

### Installation

1. **Clone the repository**

```bash
git clone <repository-url>
cd HybridCI
```

2. **Create virtual environment**

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install dependencies**

```bash
pip install flask pytest
```

4. **Initialize database**

```bash
python -c "from dashboard.models import init_db; init_db()"
```

### Running the Dashboard

```bash
cd HybridCI
python dashboard/app.py
```

Then open http://localhost:5000 in your browser.

### Running Tests

```bash
# Run language-aware cache tests
pytest ci_engine/test_language_aware.py -v

# Run sample repository tests
pytest sample_repo/tests/ -v
```

## Usage Examples

### Basic Pipeline Execution

```python
from ci_engine.pipeline_runner import run_pipeline
from ci_engine.test_mapper import generate_test_map

# Generate test mappings
TEST_MAP = generate_test_map("tests/", "src/")

# Run with language-aware caching (default)
result = run_pipeline(TEST_MAP, {})

print(f"Tests run: {len(result['tests'])}")
print(f"Time: {result['time']:.2f}s")
print(f"Cache hit: {result['cache_hit']}")
print(f"Mode: {result['mode']}")
print(f"Languages: {result.get('languages', [])}")
```

### Language-Aware Operations

```python
from ci_engine.language_utils import get_language_stats, analyze_file_impact

# Analyze project languages
stats = get_language_stats()
print(stats)

# Analyze file impact
impact = analyze_file_impact("src/utils.py")
print(impact)
# {
#     'language': 'python',
#     'filename': 'utils.py',
#     'is_test': False,
#     'is_config': False,
#     'is_shared': True,
#     'estimated_impact': 'high'
# }
```

## Dashboard Routes

| Route              | Method | Description                 |
| ------------------ | ------ | --------------------------- |
| `/`                | GET    | Main dashboard with metrics |
| `/run`             | GET    | Execute CI pipeline         |
| `/runs`            | GET    | View run history            |
| `/baseline`        | GET    | Run baseline (all tests)    |
| `/cache-stats`     | GET    | Cache statistics dashboard  |
| `/cache-stats-api` | GET    | Cache stats API (JSON)      |

## Key Components

### Cache Manager (`cache_manager.py`)

Manages both standard and language-aware caching:

```python
from ci_engine.cache_manager import (
    get_file_language,
    load_language_aware_cache,
    save_language_aware_cache
)

# Detect language
lang = get_file_language("main.py")  # Returns: "python"

# Language-aware caching
save_language_aware_cache("cache_key", data, "python")
result = load_language_aware_cache("cache_key", "python")
```

### Change Detector (`change_detector.py`)

Identifies what changed using git:

```python
from ci_engine.change_detector import get_changed_files_by_language

language_map, all_files = get_changed_files_by_language()
# {
#     'python': ['src/main.py', 'src/auth.py'],
#     'javascript': ['src/app.js']
# }
```

### Pipeline Runner (`pipeline_runner.py`)

Orchestrates test selection and execution:

```python
from ci_engine.pipeline_runner import run_pipeline

# Language-aware mode (default)
result = run_pipeline(TEST_MAP, DEP_GRAPH, language_aware=True)

# Standard mode
result = run_pipeline(TEST_MAP, DEP_GRAPH, language_aware=False)
```

## Performance

### Example Metrics

```
Baseline (all tests):           45.2s
HybridCI (single language):     8.3s   (82% faster)
HybridCI (language-aware):      12.1s  (73% faster)
Cache hit (language-aware):     0.2s   (99% faster)
```

### Why Language-Aware Caching Works

1. **Isolation**: Python changes don't invalidate JavaScript caches
2. **Granularity**: Per-language caches increase hit rate for multi-language projects
3. **Efficiency**: Smaller per-language cache datasets load faster
4. **Scalability**: Works well for monorepos with mixed language codebases

## Database Schema

### runs table

```sql
CREATE TABLE runs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    tests_run INTEGER,
    time_taken REAL,
    cache_hit INTEGER,
    mode TEXT,                 -- 'hybrid', 'baseline', 'language_aware'
    languages TEXT,            -- JSON array of languages
    language_breakdown TEXT    -- JSON breakdown of tests per language
)
```

## Configuration

### Environment Variables

```bash
# Enable/disable language-aware caching (default: enabled)
export CI_LANGUAGE_AWARE=true

# Cache directory (default: .ci_cache)
export CI_CACHE_DIR=.ci_cache

# Flask environment
export FLASK_ENV=development
export FLASK_DEBUG=1
```

## Supported Languages

- **Python** (.py)
- **JavaScript** (.js)
- **TypeScript** (.ts, .tsx)
- **Java** (.java, .class)
- **C#** (.cs)
- **C/C++** (.c, .cpp, .h)
- **Go** (.go)
- **Rust** (.rs)
- **Ruby** (.rb)
- **PHP** (.php)
- **Swift** (.swift)
- **Kotlin** (.kt)
- **Scala** (.scala)

## Testing

### Unit Tests

```bash
# Language-aware feature tests
pytest ci_engine/test_language_aware.py -v

# Full test suite
pytest -v
```

### Coverage Report

```bash
pytest --cov=ci_engine --cov-report=html
```

## Troubleshooting

### Cache Not Hitting

1. Check changed files detection: `git diff --name-only HEAD~1`
2. Verify language detection: Check `.ci_cache/language_aware/` directory
3. Clear caches if needed: `rm -rf .ci_cache/`
4. Check database: `sqlite3 ci.db "SELECT * FROM runs LIMIT 5;"`

### Performance Issues

- Monitor cache size: `du -sh .ci_cache/`
- Check database size: `du -sh ci.db`
- Review git history depth
- Clear old cache entries

### Port Already in Use

```bash
# Change Flask port
python dashboard/app.py --port 5001
```

## Advanced Configuration

See [LANGUAGE_AWARE_CACHING.md](./LANGUAGE_AWARE_CACHING.md) for detailed documentation on:

- Language detection customization
- Cache operations and management
- Performance tuning
- Custom language support
- Migration guides

## Architecture Decisions

### Why Language-Aware Caching?

1. **Better Cache Hits**: Multi-language projects benefit from isolated caches
2. **Scalability**: Smaller per-language cache datasets
3. **Flexibility**: Can optimize per-language test runners
4. **Insights**: Language-specific metrics and analytics
5. **Future-Proof**: Foundation for language-specific strategies

### Why Flask Dashboard?

- Lightweight and fast
- Real-time metrics
- Easy integration with Python backend
- Modern responsive UI
- No external dependencies beyond Flask

## Contributing

1. Create feature branch: `git checkout -b feature/amazing-feature`
2. Write tests for new functionality
3. Update documentation
4. Submit pull request

### Adding New Language Support

1. Add extension to `LANGUAGE_EXTENSIONS` in `cache_manager.py`
2. Add test cases in `test_language_aware.py`
3. Update documentation
4. Test cache operations work correctly

## Roadmap

- [ ] Language-specific test runner auto-selection
- [ ] Cross-language dependency analysis
- [ ] Performance benchmarking per language
- [ ] Cache compression
- [ ] Distributed caching support
- [ ] Integration with popular CI/CD platforms (GitHub Actions, GitLab CI, etc.)
- [ ] Machine learning-based test prediction
- [ ] Real-time collaboration features

## License

MIT License - See LICENSE file for details

## Support

- **Documentation**: [LANGUAGE_AWARE_CACHING.md](./LANGUAGE_AWARE_CACHING.md)
- **Issues**: Create an issue on GitHub
- **Discussions**: Start a discussion for questions

## Acknowledgments

- Built with Python, Flask, and Chart.js
- Inspired by intelligent test selection approaches in modern CI/CD systems
- Language detection based on common file extension mappings

---

**HybridCI** - Making CI/CD smarter, faster, and more efficient.
