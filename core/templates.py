"""
Starter code templates and boilerplates for CodeTyper.
Provides quick 1-click scaffolding for competitive programming, coding interviews,
and project skeletons across major programming languages.
"""

from typing import Dict, List, NamedTuple


class CodeTemplate(NamedTuple):
    title: str
    language_id: str
    content: str


STARTER_TEMPLATES: List[CodeTemplate] = [
    # ── Python ──
    CodeTemplate(
        title="Python: Fast I/O & Main",
        language_id="python",
        content="""import sys

def main():
    input = sys.stdin.read
    data = input().split()
    if not data:
        return
    # Process inputs here
    print("Result")

if __name__ == "__main__":
    main()
""",
    ),
    CodeTemplate(
        title="Python: LeetCode Solution",
        language_id="python",
        content="""class Solution:
    def solve(self, nums: list[int], target: int) -> int:
        # Implementation
        return 0
""",
    ),
    # ── C++ ──
    CodeTemplate(
        title="C++: Competitive Fast I/O",
        language_id="cpp",
        content="""#include <iostream>
#include <vector>
#include <string>
#include <algorithm>

using namespace std;

void solve() {
    // Solution logic
}

int main() {
    ios_base::sync_with_stdio(false);
    cin.tie(NULL);
    
    int t = 1;
    // cin >> t;
    while (t--) {
        solve();
    }
    return 0;
}
""",
    ),
    # ── Java ──
    CodeTemplate(
        title="Java: FastScanner Main",
        language_id="java",
        content="""import java.io.BufferedReader;
import java.io.InputStreamReader;
import java.util.StringTokenizer;

public class Main {
    public static void main(String[] args) throws Exception {
        BufferedReader br = new BufferedReader(new InputStreamReader(System.in));
        String line = br.readLine();
        if (line != null) {
            System.out.println("Result: " + line);
        }
    }
}
""",
    ),
    # ── Rust ──
    CodeTemplate(
        title="Rust: Fast I/O Skeleton",
        language_id="rust",
        content="""use std::io::{self, Read};

fn main() {
    let mut buffer = String::new();
    io::stdin().read_to_string(&mut buffer).unwrap();
    let mut words = buffer.split_whitespace();

    if let Some(first) = words.next() {
        println!("Input: {}", first);
    }
}
""",
    ),
    # ── Go ──
    CodeTemplate(
        title="Go: Fast Scanner Main",
        language_id="go",
        content="""package main

import (
	"bufio"
	"fmt"
	"os"
)

func main() {
	scanner := bufio.NewScanner(os.Stdin)
	for scanner.Scan() {
		line := scanner.Text()
		fmt.Println("Processed:", line)
	}
}
""",
    ),
    # ── JavaScript / TypeScript ──
    CodeTemplate(
        title="TypeScript: Starter",
        language_id="typescript",
        content="""function solve(inputs: string[]): void {
    console.log("Output:", inputs.length);
}

solve(["test1", "test2"]);
""",
    ),
    # ── C ──
    CodeTemplate(
        title="C: Standard Main",
        language_id="c",
        content="""#include <stdio.h>
#include <stdlib.h>
#include <string.h>

int main(int argc, char *argv[]) {
    printf("Hello from C\\n");
    return 0;
}
""",
    ),
    # ── SQL ──
    CodeTemplate(
        title="SQL: Schema & Query",
        language_id="sql",
        content="""CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(50) NOT NULL UNIQUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

SELECT * FROM users ORDER BY id DESC LIMIT 10;
""",
    ),
    # ── Algorithms & Patterns ──
    CodeTemplate(
        title="Python: LRU Cache & Helper",
        language_id="python",
        content="""from collections import OrderedDict

class LRUCache:
    def __init__(self, capacity: int):
        self.cap = capacity
        self.cache = OrderedDict()

    def get(self, key: int) -> int:
        if key not in self.cache:
            return -1
        self.cache.move_to_end(key)
        return self.cache[key]

    def put(self, key: int, value: int) -> None:
        if key in self.cache:
            self.cache.move_to_end(key)
        self.cache[key] = value
        if len(self.cache) > self.cap:
            self.cache.popitem(last=False)
""",
    ),
    CodeTemplate(
        title="C++: Binary Search & Graph BFS",
        language_id="cpp",
        content="""#include <iostream>
#include <vector>
#include <queue>

using namespace std;

int binary_search(const vector<int>& arr, int target) {
    int low = 0, high = arr.size() - 1;
    while (low <= high) {
        int mid = low + (high - low) / 2;
        if (arr[mid] == target) return mid;
        if (arr[mid] < target) low = mid + 1;
        else high = mid - 1;
    }
    return -1;
}

void bfs(int start, const vector<vector<int>>& adj) {
    vector<bool> visited(adj.size(), false);
    queue<int> q;
    visited[start] = true;
    q.push(start);

    while (!q.empty()) {
        int u = q.front();
        q.pop();
        for (int v : adj[u]) {
            if (!visited[v]) {
                visited[v] = true;
                q.push(v);
            }
        }
    }
}
""",
    ),
    CodeTemplate(
        title="Bash: Robust Script Skeleton",
        language_id="sh",
        content="""#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
echo "==> Running script from ${SCRIPT_DIR}..."

main() {
    echo "Done."
}

main "$@"
""",
    ),
]



def get_templates_for_language(lang_id: str) -> List[CodeTemplate]:
    """Return all templates matching the given language ID."""
    return [t for t in STARTER_TEMPLATES if t.language_id == lang_id]


def get_all_templates() -> List[CodeTemplate]:
    """Return all available templates."""
    return STARTER_TEMPLATES
