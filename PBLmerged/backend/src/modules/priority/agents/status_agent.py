"""StatusAgent - 用户状态评估"""


class StatusAgent:
    def __init__(self):
        self.name = "StatusAgent"

    def analyze(self, user_state):
        energy = user_state.get('energy', 5)
        emotion = user_state.get('emotion', 'neutral')
        available_time = user_state.get('available_time', 60)
        environment = user_state.get('environment', 'home')

        emotion_factor = {'happy': 1.2, 'neutral': 1.0, 'sad': 0.7, 'stressed': 0.6}
        effective_energy = energy * emotion_factor.get(emotion, 1.0)

        environment_score = {'home': 10, 'office': 8, 'cafe': 6, 'travel': 3}
        env_score = environment_score.get(environment, 5)

        overall_score = (effective_energy / 10 * 0.5 +
                         available_time / 240 * 0.3 +
                         env_score / 10 * 0.2)

        if effective_energy >= 8:
            recommended_task_type = "需要高度专注的复杂任务"
        elif effective_energy >= 5:
            recommended_task_type = "常规任务"
        else:
            recommended_task_type = "简单、重复性任务"

        emotion_advice = {
            'happy': "状态极佳！适合处理需要创造力的任务。",
            'neutral': "状态正常，按计划执行即可。",
            'sad': "建议先处理简单任务，稍后调整。",
            'stressed': "建议先做放松活动，或处理机械性任务。",
        }

        return {
            'energy': energy,
            'effective_energy': round(effective_energy, 1),
            'emotion': emotion,
            'available_time_minutes': available_time,
            'environment': environment,
            'overall_score': round(overall_score, 2),
            'productivity_estimate': self._estimate_productivity(effective_energy, env_score),
            'recommended_task_type': recommended_task_type,
            'advice': emotion_advice.get(emotion, "保持专注！"),
            'warnings': self._generate_warnings(user_state),
        }

    def _estimate_productivity(self, effective_energy, env_score):
        return min(100, max(0, int((effective_energy / 10 * 0.6 + env_score / 10 * 0.4) * 100)))

    def _generate_warnings(self, user_state):
        warnings = []
        if user_state.get('energy', 5) < 3:
            warnings.append("精力严重不足，建议先休息")
        if user_state.get('emotion') == 'stressed':
            warnings.append("压力过大，考虑短暂休息")
        if user_state.get('available_time', 60) < 30:
            warnings.append("可用时间较短，建议处理紧急任务")
        if user_state.get('environment') == 'travel':
            warnings.append("当前环境不适合深度工作")
        return warnings
