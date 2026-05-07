import os
import random

def create_dir(path):
    os.makedirs(path, exist_ok=True)

def generate_python(base_path, num_modules=100):
    src_path = os.path.join(base_path, 'python', 'src')
    test_path = os.path.join(base_path, 'python', 'tests')
    create_dir(src_path)
    create_dir(test_path)

    # Init files
    with open(os.path.join(src_path, '__init__.py'), 'w') as f: f.write('')
    with open(os.path.join(test_path, '__init__.py'), 'w') as f: f.write('')

    for i in range(num_modules):
        # Source file
        src_file = os.path.join(src_path, f'module_{i}.py')
        with open(src_file, 'w') as f:
            f.write("import math\nimport random\nimport time\n\n")
            for j in range(20):
                f.write(f"def func_{j}(a, b):\n")
                f.write(f"    '''This is function {j} in module {i}'''\n")
                f.write(f"    result = a + b * {random.randint(1, 10)}\n")
                f.write(f"    # simulate some complex calculation\n")
                f.write(f"    for _ in range(10):\n")
                f.write(f"        result += math.sin(a) + math.cos(b)\n")
                f.write(f"    return result\n\n")

        # Test file
        test_file = os.path.join(test_path, f'test_module_{i}.py')
        with open(test_file, 'w') as f:
            f.write("import pytest\n")
            f.write(f"from src.module_{i} import *\n\n")
            for j in range(20):
                f.write(f"def test_func_{j}():\n")
                f.write(f"    assert func_{j}(1, 2) is not None\n")
                f.write(f"    assert func_{j}(0, 0) == 0\n\n")

    # requirements
    with open(os.path.join(base_path, 'python', 'requirements.txt'), 'w') as f:
        f.write("pytest==7.4.3\n")


def generate_java(base_path, num_classes=100):
    src_path = os.path.join(base_path, 'java', 'src', 'main', 'java', 'com', 'demo')
    test_path = os.path.join(base_path, 'java', 'src', 'test', 'java', 'com', 'demo')
    create_dir(src_path)
    create_dir(test_path)

    for i in range(num_classes):
        # Source file
        with open(os.path.join(src_path, f'Service{i}.java'), 'w') as f:
            f.write("package com.demo;\n\n")
            f.write(f"public class Service{i} {{\n")
            for j in range(20):
                f.write(f"    public double method{j}(double a, double b) {{\n")
                f.write(f"        double result = a + b * {random.randint(1, 10)};\n")
                f.write(f"        for(int k=0; k<10; k++) {{\n")
                f.write(f"            result += Math.sin(a) + Math.cos(b);\n")
                f.write(f"        }}\n")
                f.write(f"        return result;\n")
                f.write(f"    }}\n")
            f.write("}\n")

        # Test file
        with open(os.path.join(test_path, f'Service{i}Test.java'), 'w') as f:
            f.write("package com.demo;\n\n")
            f.write("import org.junit.jupiter.api.Test;\n")
            f.write("import static org.junit.jupiter.api.Assertions.*;\n\n")
            f.write(f"public class Service{i}Test {{\n")
            for j in range(20):
                f.write(f"    @Test\n")
                f.write(f"    public void testMethod{j}() {{\n")
                f.write(f"        Service{i} service = new Service{i}();\n")
                f.write(f"        assertNotNull(service.method{j}(1.0, 2.0));\n")
                f.write(f"        assertEquals(0.0, service.method{j}(0.0, 0.0), 0.001);\n")
                f.write(f"    }}\n")
            f.write("}\n")
    
    # pom.xml
    with open(os.path.join(base_path, 'java', 'pom.xml'), 'w') as f:
        f.write('''<?xml version="1.0" encoding="UTF-8"?>
<project xmlns="http://maven.apache.org/POM/4.0.0"
         xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
         xsi:schemaLocation="http://maven.apache.org/POM/4.0.0 http://maven.apache.org/xsd/maven-4.0.0.xsd">
    <modelVersion>4.0.0</modelVersion>
    <groupId>com.demo</groupId>
    <artifactId>demo-java</artifactId>
    <version>1.0-SNAPSHOT</version>
    <properties>
        <maven.compiler.source>11</maven.compiler.source>
        <maven.compiler.target>11</maven.compiler.target>
    </properties>
    <dependencies>
        <dependency>
            <groupId>org.junit.jupiter</groupId>
            <artifactId>junit-jupiter-engine</artifactId>
            <version>5.9.2</version>
            <scope>test</scope>
        </dependency>
    </dependencies>
</project>''')


def generate_js(base_path, num_modules=100):
    src_path = os.path.join(base_path, 'js', 'src')
    test_path = os.path.join(base_path, 'js', 'tests')
    create_dir(src_path)
    create_dir(test_path)

    for i in range(num_modules):
        # Source file
        with open(os.path.join(src_path, f'module{i}.js'), 'w') as f:
            for j in range(20):
                f.write(f"function func{j}(a, b) {{\n")
                f.write(f"    let result = a + b * {random.randint(1, 10)};\n")
                f.write(f"    for(let k=0; k<10; k++) {{\n")
                f.write(f"        result += Math.sin(a) + Math.cos(b);\n")
                f.write(f"    }}\n")
                f.write(f"    return result;\n")
                f.write(f"}}\n\n")
            exports = ", ".join([f"func{j}" for j in range(20)])
            f.write(f"module.exports = {{ {exports} }};\n")

        # Test file
        with open(os.path.join(test_path, f'module{i}.test.js'), 'w') as f:
            f.write(f"const module{i} = require('../src/module{i}');\n\n")
            for j in range(20):
                f.write(f"test('test func{j} in module{i}', () => {{\n")
                f.write(f"    expect(module{i}.func{j}(1, 2)).toBeDefined();\n")
                f.write(f"    expect(module{i}.func{j}(0, 0)).toBe(0);\n")
                f.write(f"}});\n\n")
    
    # package.json
    with open(os.path.join(base_path, 'js', 'package.json'), 'w') as f:
        f.write('''{
  "name": "demo-js",
  "version": "1.0.0",
  "scripts": {
    "test": "jest"
  },
  "devDependencies": {
    "jest": "^29.5.0"
  }
}''')


def generate_docker(base_path):
    with open(os.path.join(base_path, 'Dockerfile'), 'w') as f:
        f.write('''# Multi-stage Dockerfile for caching demo
# PYTHON LAYER
FROM python:3.9-slim AS python-base
WORKDIR /app/python
COPY python/requirements.txt .
RUN pip install -r requirements.txt
COPY python/ .
# RUN pytest

# JAVA LAYER
FROM maven:3.8-openjdk-11 AS java-base
WORKDIR /app/java
COPY java/pom.xml .
RUN mvn dependency:go-offline
COPY java/ .
# RUN mvn test

# JS LAYER
FROM node:18-alpine AS js-base
WORKDIR /app/js
COPY js/package.json .
RUN npm install
COPY js/ .
# RUN npm test
''')

if __name__ == "__main__":
    base_dir = "repos/demo_project"
    print(f"Generating large-scale demo project at {base_dir}...")
    create_dir(base_dir)
    generate_python(base_dir, num_modules=100) # 100 * 20 functions * 8 lines = ~16k lines
    generate_java(base_dir, num_classes=100) # 100 * 20 methods * 8 lines = ~16k lines
    generate_js(base_dir, num_modules=100) # 100 * 20 functions * 8 lines = ~16k lines
    generate_docker(base_dir)
    print("Done! Demo project generation complete.")
