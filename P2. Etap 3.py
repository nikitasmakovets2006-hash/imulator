import os
import sys
from collections import deque
from typing import Dict, List, Set

# Конфигурация (простая версия)
CONFIG = {
    'package_name': 'A',
    'test_mode': True,
    'graph_file': 'test_graph.txt',
    'filter_substring': 'D'
}

class DependencyGraph:
    def __init__(self, config):
        self.config = config
        self.graph = {}
        self.visited = set()
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
                            dependencies = [d.strip() for d in deps.split(',')]
                            graph[package] = dependencies
            return graph
        except FileNotFoundError:
            print(f" Файл {self.config['graph_file']} не найден!")
            print("Создайте файл test_graph.txt с примером:")
            print("A: B, C")
            print("B: C, D")
            print("C: E")
            print("D: A  # Цикл!")
            print("E:")
            sys.exit(1)

    def should_filter(self, package: str) -> bool:
        """Проверка фильтрации пакета"""
        filter_str = self.config['filter_substring']
        return filter_str and filter_str in package

    def bfs_build_graph(self, start_package: str) -> Dict[str, List[str]]:
        test_graph = self.load_test_graph()
        result_graph = {}
        queue = deque([start_package])
        visited = set()

        print(" Построение графа зависимостей...")

        while queue:
            current = queue.popleft()

            if current in visited:
                continue
            visited.add(current)

            # Пропускаем отфильтрованные пакеты
            if self.should_filter(current):
                result_graph[current] = []
                print(f" Пропущен (фильтр): {current}")
                continue

            # Получаем зависимости
            dependencies = test_graph.get(current, [])

            # Фильтруем зависимости
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
                print(f"  Обнаружен цикл: {current} -> {current}")

        return result_graph

    def display_graph(self, graph: Dict[str, List[str]]):
        """Отображение графа"""
        print("\n" + "="*50)
        print(" ГРАФ ЗАВИСИМОСТЕЙ")
        print("="*50)

        for package, deps in graph.items():
            if deps:
                print(f"{package} -> {', '.join(deps)}")
            else:
                print(f"{package} -> (нет зависимостей)")

        if self.cycles:
            print(f"\n Обнаружены циклы: {', '.join(self.cycles)}")

        print(f"\n Статистика:")
        print(f"   Всего пакетов: {len(graph)}")
        print(f"   Циклов: {len(self.cycles)}")
        print(f"   Фильтр: '{self.config['filter_substring']}'")

def create_test_graph_file():
    """Создание тестового файла графа"""
    content = """# Тестовый граф зависимостей
# Формат: Пакет: Зависимость1, Зависимость2, ...
A: B, C
B: C, D
C: E, F
D: A  # Цикл A->B->D->A
E: G
F: 
G: H
H:"""

    with open('test_graph.txt', 'w') as f:
        f.write(content)
    print(" Создан тестовый файл: test_graph.txt")

def main():
    # Создаем тестовый файл если его нет
    if not os.path.exists('test_graph.txt'):
        create_test_graph_file()

    # Запускаем построение графа
    analyzer = DependencyGraph(CONFIG)
    graph = analyzer.bfs_build_graph(CONFIG['package_name'])
    analyzer.display_graph(graph)

    # Демонстрация разных сценариев
    print("\n" + "="*50)
    print("ТЕСТОВЫЕ СЦЕНАРИИ")
    print("="*50)

    # Тест 1: Без фильтра
    print("\n1. Без фильтра (пакет A):")
    CONFIG['filter_substring'] = ''
    analyzer1 = DependencyGraph(CONFIG)
    graph1 = analyzer1.bfs_build_graph('A')
    print(f"   Пакетов: {len(graph1)}, Циклов: {len(analyzer1.cycles)}")

    # Тест 2: С фильтром 'D'
    print("\n2. С фильтром 'D' (пакет A):")
    CONFIG['filter_substring'] = 'D'
    analyzer2 = DependencyGraph(CONFIG)
    graph2 = analyzer2.bfs_build_graph('A')
    print(f"   Пакетов: {len(graph2)}, Циклов: {len(analyzer2.cycles)}")

    # Тест 3: Другой стартовый пакет
    print("\n3. Пакет C (без фильтра):")
    CONFIG['filter_substring'] = ''
    analyzer3 = DependencyGraph(CONFIG)
    graph3 = analyzer3.bfs_build_graph('C')
    print(f"   Пакетов: {len(graph3)}, Циклов: {len(analyzer3.cycles)}")

if __name__ == "__main__":
    main()