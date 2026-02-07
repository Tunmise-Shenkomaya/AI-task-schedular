"""
AI-powered Task Dependency Analyzer
Uses OpenAI to semantically understand task relationships and auto-detect dependencies
Falls back to keyword-based analysis if API is unavailable
"""

import json
import os
from typing import List, Dict, Tuple, Optional, Set
from models import Task, ExecutionPlan, TaskStatus

# Try to import OpenAI, but make it optional
try:
    from openai import OpenAI
    HAS_OPENAI = True
except ImportError:
    HAS_OPENAI = False


class AITaskPlanner:
    """
    AI-powered planner that uses semantic analysis to detect task dependencies.
    Falls back to keyword-based analysis if OpenAI API is unavailable.
    """
    
    def __init__(self, api_key: str = None):
        """
        Initialize the AI planner.
        
        Args:
            api_key: OpenAI API key (defaults to OPENAI_API_KEY environment variable)
        """
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        self.client = None
        self.use_ai = False
        
        if HAS_OPENAI and self.api_key:
            try:
                self.client = OpenAI(api_key=self.api_key)
                self.use_ai = True
            except Exception as e:
                print(f"Warning: Could not initialize OpenAI client: {e}")
                print("Falling back to keyword-based dependency analysis")
    
    def analyze_dependencies(self, tasks: List[Task]) -> Dict[int, Set[int]]:
        """
        Use AI to analyze task relationships and determine dependencies.
        Falls back to keyword analysis if AI is unavailable.
        
        Args:
            tasks: List of Task objects
            
        Returns:
            Dictionary mapping task index to set of task indices that must come BEFORE it
        """
        if len(tasks) <= 1:
            return {i: set() for i in range(len(tasks))}
        
        # Try AI-powered analysis first
        if self.use_ai:
            try:
                return self._analyze_with_ai(tasks)
            except Exception as e:
                print(f"AI analysis failed: {e}. Falling back to keyword analysis.")
        
        # Fall back to keyword-based analysis
        return self._analyze_with_keywords(tasks)
    
    def _analyze_with_ai(self, tasks: List[Task]) -> Dict[int, Set[int]]:
        """Analyze dependencies using OpenAI API."""
        task_descriptions = "\n".join(
            [f"{i+1}. {task.name}: {task.description}" for i, task in enumerate(tasks)]
        )
        
        prompt = f"""Analyze the following tasks and determine their PREREQUISITE dependencies.
For each task, identify which OTHER tasks must be completed BEFORE it can be started.

Tasks:
{task_descriptions}

Think step by step about what must happen first logically. For example:
- You must "research" before you can "write"
- You must "write" before you can "submit"
- You must "cook" before you can "eat"

Return ONLY valid JSON in this format (no other text):
{{
  "dependencies": {{
    "1": [],
    "2": [1],
    "3": [1, 2],
    "4": [3]
  }}
}}

Where:
- The key is the task number (1-based)
- The value is a list of task numbers that must be completed BEFORE this task
- An empty list means no prerequisites

Important: Only include task numbers between 1 and {len(tasks)}"""

        response = self.client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3
        )
        
        response_text = response.choices[0].message.content.strip()
        
        # Extract JSON from response
        try:
            data = json.loads(response_text)
            deps = data.get("dependencies", {})
            
            # Convert string keys to integers and adjust from 1-based to 0-based indexing
            result = {}
            for i in range(len(tasks)):
                key = str(i + 1)
                if key in deps:
                    # Convert to 0-based indices
                    result[i] = set(x - 1 for x in deps[key] if 1 <= x <= len(tasks))
                else:
                    result[i] = set()
            
            return result
        except json.JSONDecodeError:
            print("Failed to parse AI response. Falling back to keywords.")
            return self._analyze_with_keywords(tasks)
    
    def _analyze_with_keywords(self, tasks: List[Task]) -> Dict[int, Set[int]]:
        """
        Keyword-based dependency analysis as fallback.
        Determines which tasks must come before others based on action sequences.
        """
        dependencies = {i: set() for i in range(len(tasks))}
        
        # Define action sequence priorities (lower number = must come first)
        action_phases = {
            # Planning and preparation phase
            "start": 1,
            "begin": 1,
            "plan": 1,
            "think": 1,
            
            # Research and analysis phase
            "research": 2,
            "analyze": 2,
            "study": 2,
            "learn": 2,
            "gather": 2,
            "collect": 2,
            
            # Design phase
            "design": 3,
            "design mockup": 3,
            "sketch": 3,
            "blueprint": 3,
            
            # Implementation/Writing phase
            "write": 4,
            "code": 4,
            "implement": 4,
            "build": 4,
            "develop": 4,
            "prepare": 4,
            "cook": 4,
            
            # Preparation for completion
            "set": 5,
            "arrange": 5,
            
            # Testing and review phase
            "test": 6,
            "review": 6,
            "check": 6,
            "quality": 6,
            
            # Submission/Publishing phase
            "submit": 7,
            "publish": 7,
            "launch": 7,
            "deploy": 7,
            "turn in": 7,
            
            # Final consumption
            "eat": 8,
            "enjoy": 8,
            "use": 8,
            "market": 9,
            
            # Rest phase
            "sleep": 10,
            "rest": 10,
            "relax": 10,
        }
        
        # Find the phase for each task
        task_phases = {}
        for i, task in enumerate(tasks):
            task_text = (task.name + " " + task.description).lower()
            
            min_phase = float('inf')
            for action, phase in action_phases.items():
                if action in task_text:
                    min_phase = min(min_phase, phase)
            
            task_phases[i] = min_phase if min_phase != float('inf') else 5
        
        # Now determine dependencies: if task i has a higher phase than task j,
        # then j must come before i
        for i in range(len(tasks)):
            for j in range(len(tasks)):
                if i != j:
                    # If task j has a lower phase number, it should come before task i
                    if task_phases[j] < task_phases[i]:
                        dependencies[i].add(j)
        
        return dependencies
    
    def generate_plan(self, tasks: List[Task]) -> Tuple[ExecutionPlan, Dict]:
        """
        Generate an execution plan based on task dependencies.
        
        Args:
            tasks: List of Task objects
            
        Returns:
            Tuple of (ExecutionPlan, thinking_process dictionary)
        """
        thinking = {
            "total_tasks": len(tasks),
            "stages": []
        }
        
        if not tasks:
            plan = ExecutionPlan(execution_order=[], is_valid=True)
            thinking["final_plan"] = "No tasks to execute."
            return plan, thinking
        
        # Stage 1: Analyze dependencies
        thinking["stages"].append("STAGE 1: AI is analyzing task relationships...")
        dependencies = self.analyze_dependencies(tasks)
        
        deps_str = ""
        for i, task in enumerate(tasks):
            if dependencies[i]:
                prereqs = [tasks[j].name for j in dependencies[i]]
                deps_str += f"\n• {task.name} requires: {', '.join(prereqs)}"
            else:
                deps_str += f"\n• {task.name} requires: nothing (can start immediately)"
        
        thinking["stages"].append(f"Detected dependencies:{deps_str}")
        
        # Stage 2: Perform topological sort
        thinking["stages"].append("\nSTAGE 2: Ordering tasks by dependencies...")
        ordered_indices = self._topological_sort(dependencies, len(tasks))
        
        if ordered_indices is None:
            plan = ExecutionPlan(
                execution_order=[],
                is_valid=False,
                error_message="Circular dependency detected among tasks"
            )
            thinking["final_plan"] = "ERROR: Circular dependency detected"
            return plan, thinking
        
        ordered_tasks = [tasks[i] for i in ordered_indices]
        
        # Stage 3: Create execution plan
        thinking["stages"].append(f"\nSTAGE 3: Final execution order determined")
        
        # Create execution plan
        plan = ExecutionPlan(
            execution_order=[task.id for task in ordered_tasks],
            is_valid=True,
            tasks={task.id: task for task in ordered_tasks}
        )
        
        final_order = " → ".join([t.name for t in ordered_tasks])
        thinking["final_plan"] = f"\nFINAL EXECUTION PLAN:\nExecution order: {final_order}"
        thinking["stages"].append(thinking["final_plan"])
        
        return plan, thinking
    
    def _topological_sort(self, dependencies: Dict[int, Set[int]], num_tasks: int) -> Optional[List[int]]:
        """
        Perform topological sort using Kahn's algorithm (BFS-based).
        This is more intuitive for our use case.
        
        Args:
            dependencies: Dictionary where key=task, value=set of tasks that must come before it
            num_tasks: Total number of tasks
            
        Returns:
            List of task indices in correct execution order, or None if cycle detected
        """
        # Build in-degree count and adjacency list
        in_degree = [0] * num_tasks
        adjacency = {i: [] for i in range(num_tasks)}
        
        # in_degree[i] = number of tasks that must come before task i
        for task_idx, prereqs in dependencies.items():
            in_degree[task_idx] = len(prereqs)
            for prereq in prereqs:
                adjacency[prereq].append(task_idx)
        
        # Find all tasks with no prerequisites (in_degree = 0)
        queue = [i for i in range(num_tasks) if in_degree[i] == 0]
        result = []
        
        while queue:
            # Take the first task with no prerequisites
            current = queue.pop(0)
            result.append(current)
            
            # For each task that depends on current task
            for dependent in adjacency[current]:
                in_degree[dependent] -= 1
                # If all prerequisites of dependent are done, add it to queue
                if in_degree[dependent] == 0:
                    queue.append(dependent)
        
        # If not all tasks were processed, there's a cycle
        if len(result) != num_tasks:
            return None
        
        return result
