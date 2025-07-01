# Aider REST API Testing Guide

Hướng dẫn chi tiết về cách chạy unit tests cho Aider REST API.

## 📋 Tổng quan

Test suite bao gồm:

- **Unit Tests** (`test_api_unit.py`) - Tests cho các endpoint và functionality cơ bản
- **Search/Replace Tests** (`test_search_replace.py`) - Tests cho tính năng SEARCH/REPLACE parsing
- **Streaming Tests** (`test_api_streaming.py`) - Tests cho streaming functionality và SSE

## 🚀 Cài đặt Dependencies

### 1. Cài đặt testing dependencies:

```bash
pip install -r requirements_test.txt
```

### 2. Hoặc cài đặt từng package:

```bash
pip install pytest pytest-asyncio pytest-cov coverage httpx python-multipart
```

## 🧪 Chạy Tests

### Chạy tất cả tests:

```bash
python run_tests.py all
```

### Chạy specific test files:

```bash
# Unit tests
python run_tests.py test_api_unit.py

# Search/Replace tests  
python run_tests.py test_search_replace.py

# Streaming tests
python run_tests.py test_api_streaming.py
```

### Chạy tests theo pattern:

```bash
# Chỉ chạy tests có "search" trong tên
python run_tests.py search

# Chỉ chạy tests có "streaming" trong tên
python run_tests.py streaming

# Chỉ chạy tests có "session" trong tên
python run_tests.py session
```

### Chạy với coverage report:

```bash
python run_tests.py coverage
```

## 📊 Test Coverage

Sau khi chạy tests với coverage, bạn có thể xem report:

- **Terminal report**: Hiển thị ngay sau khi chạy
- **HTML report**: Mở file `htmlcov/index.html` trong browser

Target coverage: **80%+**

## 🏗️ Cấu trúc Tests

### `test_api_unit.py`
- ✅ Health check endpoint
- ✅ Models listing
- ✅ Session management (create, delete)
- ✅ File operations (upload, sync)
- ✅ Chat functionality (mocked)
- ✅ Error handling
- ✅ Request validation

### `test_search_replace.py`
- ✅ SEARCH/REPLACE parsing
- ✅ Multiple blocks handling
- ✅ Whitespace preservation
- ✅ Special characters
- ✅ File application
- ✅ Edge cases and error handling
- ✅ Complex real-world scenarios

### `test_api_streaming.py`
- ✅ SSE format compliance
- ✅ Streaming vs non-streaming responses
- ✅ Concurrent requests
- ✅ Error handling in streaming
- ✅ Performance characteristics

## 📝 Test Markers

Sử dụng markers để chạy specific types của tests:

```bash
# Chỉ chạy unit tests
pytest -m unit

# Chỉ chạy streaming tests
pytest -m streaming

# Chỉ chạy file operation tests
pytest -m file_ops

# Chỉ chạy session management tests
pytest -m session
```

## 🔧 Advanced Testing

### Parallel Testing:

```bash
pytest -n auto test_api_unit.py test_search_replace.py
```

### với HTML report:

```bash
pytest --html=reports/report.html --self-contained-html
```

### với JSON report:

```bash
pytest --json-report --json-report-file=reports/report.json
```

### Benchmark testing:

```bash
pytest --benchmark-only
```

## 🐛 Debugging Tests

### Chạy specific test:

```bash
pytest test_api_unit.py::TestSessionManagement::test_create_session -v
```

### Chạy với pdb debugger:

```bash
pytest --pdb test_api_unit.py::TestSessionManagement::test_create_session
```

### Xem full traceback:

```bash
pytest --tb=long test_api_unit.py
```

## 📈 Performance Testing

### Measure test duration:

```bash
pytest --durations=10
```

### Profile slow tests:

```bash
pytest --durations=0 | head -20
```

## ⚙️ Configuration

Configuration được định nghĩa trong `pytest_api.ini`:

- Test discovery patterns
- Coverage settings
- Timeout settings
- Logging configuration
- Warning filters

## 🔍 Test Examples

### Example 1: Test SEARCH/REPLACE functionality

```python
def test_simple_search_replace():
    response = '''
<<<<<<< SEARCH
def hello():
    print("Hello")
=======
def hello():
    print("Hello, World!")
>>>>>>> REPLACE
'''
    
    result = simple_search_replace_parser(response)
    assert len(result) == 1
    assert "Hello, World!" in result[0][1]
```

### Example 2: Test API endpoint

```python
def test_create_session():
    response = client.post("/sessions", json={})
    assert response.status_code == 200
    data = response.json()
    assert "session_id" in data
```

## 🚨 Troubleshooting

### Common Issues:

1. **ModuleNotFoundError**: Ensure all dependencies are installed
2. **TestClient errors**: Make sure FastAPI and httpx are compatible versions
3. **Async test failures**: Ensure pytest-asyncio is installed
4. **Coverage issues**: Check that source files are in the correct path

### Debug Commands:

```bash
# Check pytest version
pytest --version

# List all available tests
pytest --collect-only

# Check test configuration
pytest --markers
```

## 📚 Additional Resources

- [Pytest Documentation](https://docs.pytest.org/)
- [FastAPI Testing](https://fastapi.tiangolo.com/tutorial/testing/)
- [Coverage.py Documentation](https://coverage.readthedocs.io/)

## 🎯 Best Practices

1. **Keep tests isolated** - Each test should be independent
2. **Use descriptive names** - Test names should explain what is being tested
3. **Mock external dependencies** - Don't make real API calls in unit tests
4. **Test edge cases** - Include tests for error conditions and edge cases
5. **Maintain good coverage** - Aim for 80%+ test coverage
6. **Run tests frequently** - Run tests before each commit

---

**Happy Testing! 🧪✨** 