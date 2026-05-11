"""RankingAgent - 排序决策"""


class RankingAgent:
    def __init__(self):
        self.name = "RankingAgent"

    def rank(self, user_state, task_analyses, status_analysis):
        sorted_tasks = sorted(task_analyses, key=lambda x: x['analysis']['priority_score'], reverse=True)

        ranked_tasks = []
        for rank, item in enumerate(sorted_tasks, 1):
            task = item['task']
            analysis = item['analysis']
            ranked_tasks.append({
                'rank': rank,
                'task_id': task.get('id'),
                'task_name': task.get('name'),
                'priority_score': analysis['priority_score'],
                'eisenhower_quadrant': analysis['eisenhower']['quadrant'],
                'estimated_time': analysis['estimated_time_minutes'],
                'deadline_info': analysis['deadline_analysis']['description'],
                'execution_advice': self._generate_execution_advice(rank, analysis, status_analysis, user_state),
                'full_analysis': analysis,
            })

        return {
            'ranked_tasks': ranked_tasks,
            'recommendation': self._generate_overall_recommendation(ranked_tasks, status_analysis, user_state),
            'execution_plan': self._create_execution_plan(ranked_tasks, user_state, status_analysis),
            'estimated_total_time': sum(t['estimated_time'] for t in ranked_tasks),
            'user_available_time': user_state.get('available_time', 0),
        }

    def _generate_execution_advice(self, rank, analysis, status_analysis, user_state):
        advices = []
        if rank == 1:
            advices.append("🎯 优先处理！这是当前最重要的任务")
        elif rank <= 3:
            advices.append(f"🔥 前{rank}优先级，今天务必完成")
        else:
            advices.append("📝 稍后处理或拆分")

        effective_energy = status_analysis.get('effective_energy', 5)
        if analysis['eisenhower']['quadrant'] == 'DO':
            if effective_energy < 5:
                advices.append("💡 虽然精力不足，但此任务紧急，先处理核心部分")
            else:
                advices.append("💪 精力充沛，趁热打铁！")

        if analysis['time_match']['match_level'] == 'tight':
            advices.append("⏱️ 时间紧张，建议专注完成")

        return " | ".join(advices)

    def _generate_overall_recommendation(self, ranked_tasks, status_analysis, user_state):
        recs = []
        total_estimated = sum(t['estimated_time'] for t in ranked_tasks)
        available_time = user_state.get('available_time', 60)

        if total_estimated > available_time:
            recs.append(f"⚠️ 所有任务预计需要 {total_estimated} 分钟，但你只有 {available_time} 分钟")
            recs.append("建议将部分任务延后或委托他人")
        else:
            recs.append(f"✅ 任务预计需要 {total_estimated} 分钟，你还剩 {available_time - total_estimated} 分钟缓冲时间")

        for warning in status_analysis.get('warnings', []) or []:
            recs.append(warning)

        eisenhower_counts = {}
        for task in ranked_tasks:
            quad = task['eisenhower_quadrant']
            eisenhower_counts[quad] = eisenhower_counts.get(quad, 0) + 1
        if eisenhower_counts.get('ELIM', 0) > 0:
            recs.append(f"💡 有 {eisenhower_counts['ELIM']} 个低优先级任务，考虑删除")

        return "\n".join(recs)

    def _create_execution_plan(self, ranked_tasks, user_state, status_analysis):
        available_time = user_state.get('available_time', 60)
        effective_energy = status_analysis.get('effective_energy', 5)

        plan = {
            'phase_1': {'name': '核心任务', 'tasks': [], 'time': 0},
            'phase_2': {'name': '次要任务', 'tasks': [], 'time': 0},
            'phase_3': {'name': '可选任务', 'tasks': [], 'time': 0},
            'buffer_time': 10,
            'rest_suggestion': None,
        }
        current_time = 0
        time_limit = available_time - plan['buffer_time']

        for task in ranked_tasks:
            task_time = task['estimated_time']
            if current_time + task_time <= time_limit:
                if task['rank'] <= 3:
                    plan['phase_1']['tasks'].append(task['task_name'])
                    plan['phase_1']['time'] += task_time
                else:
                    plan['phase_2']['tasks'].append(task['task_name'])
                    plan['phase_2']['time'] += task_time
            else:
                plan['phase_3']['tasks'].append(task['task_name'])
            current_time += task_time

        if available_time >= 120 and effective_energy < 7:
            plan['rest_suggestion'] = "长时间工作后建议休息10分钟"
        elif effective_energy < 5:
            plan['rest_suggestion'] = "精力不足，建议先休息5-10分钟"

        return plan
