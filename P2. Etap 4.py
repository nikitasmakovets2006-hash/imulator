import os
import sys
from collections import deque
from typing import Dict, List, Set, Tuple

# Конфигурация
CONFIG = {
    'package_name': 'A',
    'test_mode': True,
    'graph_file': 'test_graph.txt',
    'filter_substring': '',
    'show_load_order': True
}

class DependencyAnalyzer:
    def __init__(self, config):
        self.config = config
        self.graph = {}
        self.cycles = set()

    def load_test_graph(self) -> Dict[str, List[str]]:
        """Загрузка тестового графа из файла"""
        graph = {}
        try:
            with open(self.config['graph_file'], 'r') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#'):
                        if ':' in line:
                            package, deps = line.split(':', 1)
                            package = package.strip()
                            dependencies = [d.strip() for d in deps.split(',') if d.strip()]
                            graph[package] = dependencies
            return graph
        except FileNotFoundError:
            print(f" Файл {self.config['graph_file']} не найден!")
            sys.exit(1)

    def should_filter(self, package: str) -> bool:
        """Проверка фильтрации пакета"""
        filter_str = self.config['filter_substring']
        return filter_str and filter_str in package

    def bfs_build_graph(self, start_package: str) -> Dict[str, List[str]]:
        """Построение графа BFS"""
        test_graph = self.load_test_graph()
        result_graph = {}
        queue = deque([start_package])
        visited = set()

        while queue:
            current = queue.popleft()

            if current in visited:
                continue
            visited.add(current)

            if self.should_filter(current):
                result_graph[current] = []
                continue

            dependencies = test_graph.get(current, [])
            filtered_deps = []

            for dep in dependencies:
                if not self.should_filter(dep):
                    filtered_deps.append(dep)
                    if dep not in visited:
                        queue.append(dep)

            result_graph[current] = filtered_deps

            # Проверка циклов
            if current in dependencies:
                self.cycles.add(current)

        return result_graph

    def calculate_load_order_bfs(self, start_package: str) -> List[str]:
        """Порядок загрузки через BFS (наш метод)"""
        test_graph = self.load_test_graph()
        load_order = []
        visited = set()
        queue = deque([start_package])

        while queue:
            current = queue.popleft()
            if current in visited:
                continue

            # Добавляем в порядок загрузки ПЕРЕД обработкой зависимостей
            load_order.append(current)
            visited.add(current)

            # Добавляем зависимости в очередь
            for dep in test_graph.get(current, []):
                if not self.should_filter(dep) and dep not in visited:
                    queue.append(dep)

        return load_order

    def calculate_load_order_dfs(self, start_package: str) -> List[str]:
        """Порядок загрузки через DFS (как у реальных менеджеров)"""
        test_graph = self.load_test_graph()
        load_order = []
        visited = set()

        def dfs(package):
            if package in visited or self.should_filter(package):
                return
            visited.add(package)

            # Сначала обрабатываем все зависимости
            for dep in test_graph.get(package, []):
                dfs(dep)

            # Потом добавляем сам пакет
            load_order.append(package)

        dfs(start_package)
        return load_order

    def compare_load_orders(self, start_package: str):
        """Сравнение порядков загрузки"""
        print("\n" + "="*60)
        print(" СРАВНЕНИЕ ПОРЯДКОВ ЗАГРУЗКИ")
        print("="*60)

        # Наш метод (BFS)
        our_order = self.calculate_load_order_bfs(start_package)
        print(f"\n НАШ МЕТОД (BFS):")
        print("   " + " → ".join(our_order))

        # Метод менеджеров пакетов (DFS)
        manager_order = self.calculate_load_order_dfs(start_package)
        print(f"\n МЕНЕДЖЕРЫ ПАКЕТОВ (DFS):")
        print("   " + " → ".join(manager_order))

        # Сравнение
        print(f"\n СРАВНЕНИЕ:")
        print(f"   Совпадают: {' ДА' if our_order == manager_order else ' НЕТ'}")

        if our_order != manager_order:
            print(f"\n ПОЧЕМУ РАЗНЫЕ РЕЗУЛЬТАТЫ?")
            print("   BFS: Сначала загружает все пакеты текущего уровня")
            print("   DFS: Сначала загружает ВСЕ зависимости, потом сам пакет")
            print("   Менеджеры используют DFS для корректного разрешения зависимостей")

    def display_dependency_tree(self, start_package: str):
        """Отображение дерева зависимостей"""
        test_graph = self.load_test_graph()

        print(f"\n ДЕРЕВО ЗАВИСИМОСТЕЙ '{start_package}':")

        def print_tree(package, level=0, prefix="", visited=None):
            if visited is None:
                visited = set()

            if package in visited:
                print(f"{prefix} {package} (ЦИКЛ)")
                return

            visited.add(package)
            marker = "└── " if level > 0 else ""
            print(f"{prefix}{marker}{package}")

            deps = test_graph.get(package, [])
            for i, dep in enumerate(deps):
                is_last = i == len(deps) - 1
                new_prefix = prefix + ("    " if level == 0 else "    " if is_last else "│   ")
                print_tree(dep, level + 1, new_prefix, visited.copy())

        print_tree(start_package)

    def analyze_package(self, start_package: str):
        """Полный анализ пакета"""
        print(f"\n АНАЛИЗ ПАКЕТА: {start_package}")
        print("="*50)

        # Построение графа
        graph = self.bfs_build_graph(start_package)

        # Отображение графа
        print("\n ГРАФ ЗАВИСИМОСТЕЙ:")
        for package, deps in graph.items():
            if deps:
                print(f"   {package} → {', '.join(deps)}")
            else:
                print(f"   {package} → (нет зависимостей)")

        # Дерево зависимостей
        self.display_dependency_tree(start_package)

        # Сравнение порядков загрузки
        if self.config['show_load_order']:
            self.compare_load_orders(start_package)

        # Статистика
        print(f"\n СТАТИСТИКА:")
        print(f"   Всего пакетов: {len(graph)}")
        print(f"   Обнаружено циклов: {len(self.cycles)}")
        if self.cycles:
            print(f"   Циклы: {', '.join(self.cycles)}")

def create_test_graph_file():
    """Создание тестового файла графа"""
    content = """# Тестовый граф зависимостей
A: B, C
B: D, E
C: F, G
D: H
E: 
F: E
G: H
H:"""

    with open('test_graph.txt', 'w') as f:
        f.write(content)
    print(" Создан тестовый файл: test_graph.txt")

def main():
    # Создаем тестовый файл если его нет
    if not os.path.exists('test_graph.txt'):
        create_test_graph_file()

    analyzer = DependencyAnalyzer(CONFIG)

    print(" ЭТАП 4: ДОПОЛНИТЕЛЬНЫЕ ОПЕРАЦИИ")
    print("="*60)

    # Тест 1: Базовый анализ
    print("\n1.  БАЗОВЫЙ АНАЛИЗ (пакет A):")
    analyzer.analyze_package('A')

    # Тест 2: С фильтром
    print("\n\n2.  АНАЛИЗ С ФИЛЬТРОМ 'E' (пакет A):")
    CONFIG['filter_substring'] = 'E'
    analyzer2 = DependencyAnalyzer(CONFIG)
    analyzer2.analyze_package('A')

    # Тест 3: Другой пакет
    print("\n\n3.  АНАЛИЗ ПАКЕТА B:")
    CONFIG['filter_substring'] = ''
    analyzer3 = DependencyAnalyzer(CONFIG)
    analyzer3.analyze_package('B')

    # Тест 4: Сложный случай с циклом
    print("\n\n4.  СЛОЖНЫЙ СЛУЧАЙ С ЦИКЛОМ:")

    # Создаем граф с циклом
    cycle_content = """# Граф с циклом
A: B
B: C  
C: A  # Цикл A->B->C->A
D: E
E:"""

    with open('cycle_graph.txt', 'w') as f:
        f.write(cycle_content)

    CONFIG['graph_file'] = 'cycle_graph.txt'
    analyzer4 = DependencyAnalyzer(CONFIG)
    analyzer4.analyze_package('A')

if __name__ == "__main__":
    main()