"""AgentOrchestrator - Multi-Agent 编排器"""

from datetime import datetime

from .ranking_agent import RankingAgent
from .status_agent import StatusAgent
from .task_agent import TaskAgent


class AgentOrchestrator:
    def __init__(self):
        self.status_agent = StatusAgent()
        self.task_agent = TaskAgent()
        self.ranking_agent = RankingAgent()
        self.execution_log = []

    def run(self, user_state, tasks):
        self.execution_log = []
        start_time = datetime.now()

        self.execution_log.append({'agent': 'StatusAgent', 'step': 1, 'status': 'running', 'timestamp': start_time.isoformat()})
        status_analysis = self.status_agent.analyze(user_state)
        self.execution_log.append({'agent': 'StatusAgent', 'step': 1, 'status': 'completed'})

        self.execution_log.append({'agent': 'TaskAgent', 'step': 2, 'status': 'running', 'timestamp': datetime.now().isoformat()})
        task_analyses = []
        for task in tasks:
            analysis = self.task_agent.analyze(task, user_state, status_analysis)
            task_analyses.append({'task': task, 'analysis': analysis})
        self.execution_log.append({'agent': 'TaskAgent', 'step': 2, 'status': 'completed'})

        self.execution_log.append({'agent': 'RankingAgent', 'step': 3, 'status': 'running', 'timestamp': datetime.now().isoformat()})
        ranking_result = self.ranking_agent.rank(user_state, task_analyses, status_analysis)
        end_time = datetime.now()
        self.execution_log.append({'agent': 'RankingAgent', 'step': 3, 'status': 'completed'})

        total_time = (end_time - start_time).total_seconds()

        return {
            'success': True,
            'summary': {
                'status_summary': status_analysis,
                'total_tasks': len(tasks),
                'processing_time_ms': int(total_time * 1000),
                'recommendation': ranking_result['recommendation'],
                'execution_plan': ranking_result['execution_plan'],
            },
            'status_analysis': status_analysis,
            'task_analyses': task_analyses,
            'ranking': ranking_result['ranked_tasks'],
            'execution_log': self.execution_log,
        }

    def get_status(self):
        return {
            'agents': [
                {'name': 'StatusAgent', 'status': 'ready'},
                {'name': 'TaskAgent', 'status': 'ready'},
                {'name': 'RankingAgent', 'status': 'ready'},
            ],
            'execution_log': self.execution_log,
        }
