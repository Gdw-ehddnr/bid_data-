#!/usr/bin/env python3
"""
설치 상태 확인 스크립트
각 Pi에서 실행하여 필요한 소프트웨어가 설치되어 있는지 확인합니다.
"""
import sys
import subprocess
import os
import importlib.util


def check_command(command, name):
    """명령어가 설치되어 있는지 확인"""
    try:
        result = subprocess.run(
            [command, '--version'],
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.returncode == 0:
            version = result.stdout.strip().split('\n')[0]
            return True, version
        else:
            return False, None
    except FileNotFoundError:
        return False, None
    except Exception:
        return False, None


def check_python_package(package_name, import_name=None):
    """Python 패키지가 설치되어 있는지 확인"""
    if import_name is None:
        import_name = package_name
    
    try:
        if import_name == 'yaml':
            import yaml
        elif import_name == 'kafka':
            from kafka import KafkaProducer
        elif import_name == 'sqlalchemy':
            import sqlalchemy
        elif import_name == 'pymysql':
            import pymysql
        elif import_name == 'scrapy':
            import scrapy
        elif import_name == 'pandas':
            import pandas
        elif import_name == 'numpy':
            import numpy
        elif import_name == 'bs4':
            import bs4
        elif import_name == 'lxml':
            import lxml
        elif import_name == 'dateutil':
            from dateutil import parser
        else:
            __import__(import_name)
        return True
    except ImportError:
        return False


def check_java():
    """Java가 설치되어 있는지 확인"""
    try:
        result = subprocess.run(
            ['java', '-version'],
            capture_output=True,
            text=True,
            stderr=subprocess.STDOUT,
            timeout=5
        )
        if result.returncode == 0:
            version_line = result.stdout.split('\n')[0]
            return True, version_line
        return False, None
    except:
        return False, None


def check_kafka():
    """Kafka가 설치되어 있는지 확인"""
    kafka_paths = [
        os.path.expanduser('~/kafka/kafka_2.13-3.5.0'),
        os.path.expanduser('~/kafka/kafka_2.13-3.6.0'),
        '/opt/kafka',
    ]
    
    for path in kafka_paths:
        kafka_script = os.path.join(path, 'bin', 'kafka-topics.sh')
        if os.path.exists(kafka_script):
            return True, path
    
    # 환경 변수 확인
    kafka_home = os.environ.get('KAFKA_HOME')
    if kafka_home:
        kafka_script = os.path.join(kafka_home, 'bin', 'kafka-topics.sh')
        if os.path.exists(kafka_script):
            return True, kafka_home
    
    return False, None


def check_mysql():
    """MySQL/MariaDB가 설치되어 있는지 확인"""
    try:
        result = subprocess.run(
            ['mysql', '--version'],
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.returncode == 0:
            version = result.stdout.strip()
            return True, version
        return False, None
    except:
        return False, None


def check_project_files():
    """프로젝트 파일이 있는지 확인"""
    required_files = [
        'requirements.txt',
        'config/config.example.yaml',
        'pi1/scripts/run_spider.py',
        'pi2/scripts/run_consumer.py',
        'pi3/scripts/run_db_consumer.py',
    ]
    
    missing = []
    for file in required_files:
        if not os.path.exists(file):
            missing.append(file)
    
    return len(missing) == 0, missing


def main():
    """메인 함수"""
    print("=" * 60)
    print("설치 상태 확인")
    print("=" * 60)
    print()
    
    # Python 확인
    print("1. Python 환경")
    print("-" * 60)
    python_version = sys.version.split()[0]
    print(f"  ✓ Python: {python_version}")
    
    try:
        import pip
        print("  ✓ pip: 설치됨")
    except:
        print("  ✗ pip: 설치 필요 (sudo apt install python3-pip)")
    print()
    
    # 시스템 명령어 확인
    print("2. 시스템 소프트웨어")
    print("-" * 60)
    
    # Git
    installed, version = check_command('git', 'Git')
    if installed:
        print(f"  ✓ Git: {version}")
    else:
        print("  ✗ Git: 설치 필요")
    
    # Java
    installed, version = check_java()
    if installed:
        print(f"  ✓ Java: {version[:50]}...")
    else:
        print("  ✗ Java: 설치 필요")
    
    # MySQL
    installed, version = check_mysql()
    if installed:
        print(f"  ✓ MySQL/MariaDB: {version}")
    else:
        print("  ✗ MySQL/MariaDB: 설치 필요 (Pi3만)")
    
    # Kafka
    installed, path = check_kafka()
    if installed:
        print(f"  ✓ Kafka: {path}")
    else:
        print("  ✗ Kafka: 설치 필요 (Pi1만)")
    print()
    
    # Python 패키지 확인
    print("3. Python 패키지")
    print("-" * 60)
    
    packages = [
        ('scrapy', 'scrapy'),
        ('kafka-python', 'kafka'),
        ('pymysql', 'pymysql'),
        ('sqlalchemy', 'sqlalchemy'),
        ('pyyaml', 'yaml'),
        ('python-dateutil', 'dateutil'),
        ('pandas', 'pandas'),
        ('numpy', 'numpy'),
        ('beautifulsoup4', 'bs4'),
        ('lxml', 'lxml'),
    ]
    
    missing_packages = []
    for pkg_name, import_name in packages:
        if check_python_package(pkg_name, import_name):
            print(f"  ✓ {pkg_name}")
        else:
            print(f"  ✗ {pkg_name}: 설치 필요")
            missing_packages.append(pkg_name)
    print()
    
    # 프로젝트 파일 확인
    print("4. 프로젝트 파일")
    print("-" * 60)
    installed, missing = check_project_files()
    if installed:
        print("  ✓ 프로젝트 파일: 모두 존재")
    else:
        print(f"  ✗ 프로젝트 파일: {len(missing)}개 누락")
        for file in missing:
            print(f"    - {file}")
    print()
    
    # 요약
    print("=" * 60)
    print("요약")
    print("=" * 60)
    
    if missing_packages:
        print(f"\n⚠️  설치 필요한 Python 패키지: {len(missing_packages)}개")
        print("   실행: pip3 install --user -r requirements.txt")
    
    if not check_kafka()[0]:
        print("\n⚠️  Kafka 설치 필요 (Pi1만)")
        print("   참조: docs/KAFKA_INSTALL_GUIDE.md")
    
    if not check_mysql()[0]:
        print("\n⚠️  MySQL/MariaDB 설치 필요 (Pi3만)")
        print("   참조: docs/MARIADB_INSTALL_GUIDE.md")
    
    if not check_project_files()[0]:
        print("\n⚠️  프로젝트 파일이 누락되었습니다")
        print("   Git으로 클론하거나 복사하세요")
    
    if not missing_packages and check_kafka()[0] and check_mysql()[0] and check_project_files()[0]:
        print("\n✅ 모든 필수 소프트웨어가 설치되어 있습니다!")
        print("   다음 단계: 설정 파일 생성 및 검증")
    else:
        print("\n⚠️  일부 소프트웨어가 누락되었습니다. 위의 항목을 확인하세요.")


if __name__ == '__main__':
    main()

