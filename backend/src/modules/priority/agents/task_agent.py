"""TaskAgent - 任务特征分析"""

from datetime import datetime


class TaskAgent:
    def __init__(self):
        self.name = "TaskAgent"

    def analyze(self, task, user_state, status_analysis):
        task_id = task.get('id', 'unknown')
        task_name = task.get('name', '未命名任务')
        deadline = task.get('deadline')
        urgency = task.get('urgency', 'medium')
        importance = task.get('importance', 5)
        estimated_time = task.get('estimated_time', 30)

        deadline_analysis = self._analyze_deadline(deadline)
        eisenhower = self._classify_eisenhower(urgency, importance)
        energy_match = self._check_energy_match(estimated_time, urgency, status_analysis)
        time_match = self._check_time_match(estimated_time, user_state.get('available_time', 60))

        priority_score = self._calculate_priority_score(
            deadline_analysis['urgency_score'],
            importance,
            energy_match['score'],
            time_match['score'],
            eisenhower['priority'],
        )

        return {
            'task_id': task_id,
            'task_name': task_name,
            'estimated_time_minutes': estimated_time,
            'deadline': deadline,
            'urgency': urgency,
            'importance': importance,
            'deadline_analysis': deadline_analysis,
            'eisenhower': eisenhower,
            'energy_match': energy_match,
            'time_match': time_match,
            'priority_score': priority_score,
            'recommendation': self._generate_recommendation(energy_match, time_match, priority_score),
        }

    def _analyze_deadline(self, deadline):
        if not deadline:
            return {'has_deadline': False, 'urgency_score': 5, 'time_remaining': None, 'description': '无截止时间'}
        try:
            deadline_dt = datetime.fromisoformat(deadline.replace('Z', '+00:00'))
            now = datetime.now()
            time_remaining = deadline_dt - now
            hours_remaining = time_remaining.total_seconds() / 3600

            if hours_remaining < 0:
                urgency_score, description = 10, f"已过期 {abs(int(hours_remaining))} 小时"
            elif hours_remaining < 1:
                urgency_score, description = 9, "非常紧急！不到1小时"
            elif hours_remaining < 4:
                urgency_score, description = 7, f"紧迫，还有 {int(hours_remaining)} 小时"
            elif hours_remaining < 24:
                urgency_score, description = 5, f"今天内，还有 {int(hours_remaining)} 小时"
            elif hours_remaining < 72:
                urgency_score, description = 3, "3天内，时间充裕"
            else:
                urgency_score, description = 1, f"时间充足，还有 {int(hours_remaining/24)} 天"

            return {
                'has_deadline': True,
                'urgency_score': urgency_score,
                'time_remaining_hours': round(hours_remaining, 1),
                'description': description,
            }
        except Exception as e:
            return {'has_deadline': False, 'urgency_score': 5, 'error': str(e)}

    def _classify_eisenhower(self, urgency, importance):
        urgency_num = {'high': 8, 'medium': 5, 'low': 2}.get(urgency, 5)
        is_urgent = urgency_num >= 6
        is_important = importance >= 7
        if is_urgent and is_important:
            return {'quadrant': 'DO', 'description': '紧急且重要 → 立即执行', 'priority': 10}
        if is_urgent and not is_important:
            return {'quadrant': 'DEL', 'description': '紧急但不重要 → 尽量委托', 'priority': 6}
        if not is_urgent and is_important:
            return {'quadrant': 'SCH', 'description': '不紧急但重要 → 安排时间', 'priority': 8}
        return {'quadrant': 'ELIM', 'description': '不紧急也不重要 → 可删除', 'priority': 2}

    def _check_energy_match(self, estimated_time, urgency, status_analysis):
        effective_energy = status_analysis.get('effective_energy', 5)
        if urgency == 'high' and effective_energy < 5:
            return {'score': 2, 'match_level': 'poor', 'reason': '精力不足，难以高效完成紧急任务'}
        if estimated_time > 120 and effective_energy < 5:
            return {'score': 3, 'match_level': 'poor', 'reason': '长任务需要充沛精力，当前状态不佳'}
        if estimated_time > 60 and effective_energy < 7:
            return {'score': 5, 'match_level': 'fair', 'reason': '任务较长，可能需要中途休息'}
        return {'score': 8, 'match_level': 'good', 'reason': '任务与当前精力匹配良好'}

    def _check_time_match(self, estimated_time, available_time):
        ratio = available_time / estimated_time if estimated_time > 0 else 0
        if ratio < 1:
            return {'score': 1, 'match_level': 'insufficient', 'reason': f'时间不够！需要 {estimated_time} 分钟，但只有 {available_time} 分钟'}
        if ratio < 1.5:
            return {'score': 4, 'match_level': 'tight', 'reason': '时间紧张，刚好够用'}
        if ratio < 2.5:
            return {'score': 8, 'match_level': 'good', 'reason': '时间充裕'}
        return {'score': 10, 'match_level': 'excellent', 'reason': '时间非常充裕'}

    def _calculate_priority_score(self, urgency_score, importance, energy_score, time_score, eisenhower_priority):
        weights = {'urgency': 0.30, 'importance': 0.25, 'energy': 0.20, 'time': 0.15, 'eisenhower': 0.10}
        total = (
            urgency_score * weights['urgency']
            + importance * 2 * weights['importance']
            + energy_score * weights['energy']
            + time_score * weights['time']
            + eisenhower_priority * weights['eisenhower']
        )
        return round(total, 1)

    def _generate_recommendation(self, energy_match, time_match, priority_score):
        recs = []
        if time_match['match_level'] == 'insufficient':
            recs.append("⚠️ 时间不足，考虑拆分任务或延后")
        if energy_match['match_level'] == 'poor':
            recs.append("⚠️ 精力不足，建议稍后或分段完成")
        if priority_score >= 8:
            recs.append("✅ 强烈建议立即执行")
        elif priority_score >= 6:
            recs.append("👍 建议今天内完成")
        else:
            recs.append("📝 可延后处理")
        return " | ".join(recs) if recs else "按计划执行"
