// ==================== 模拟数据 ====================

// 教师信息
export const teachers = [
  { id: 't1', name: '王教授', avatar: '👨‍🏫', department: '教育技术学院', email: 'wang@edu.cn' },
  { id: 't2', name: '李老师', avatar: '👩‍🏫', department: '计算机科学学院', email: 'li@edu.cn' },
];

// 学生信息
export const students = [
  { id: 's1', name: '张三', avatar: '👨‍🎓', grade: '研一', major: '教育技术学', email: 'zhangsan@stu.edu.cn' },
  { id: 's2', name: '李四', avatar: '👩‍🎓', grade: '研一', major: '教育技术学', email: 'lisi@stu.edu.cn' },
  { id: 's3', name: '王五', avatar: '👨‍🎓', grade: '研二', major: '计算机科学', email: 'wangwu@stu.edu.cn' },
  { id: 's4', name: '赵六', avatar: '👩‍🎓', grade: '研一', major: '教育技术学', email: 'zhaoliu@stu.edu.cn' },
  { id: 's5', name: '钱七', avatar: '👨‍🎓', grade: '研二', major: '人工智能', email: 'qianqi@stu.edu.cn' },
  { id: 's6', name: '孙八', avatar: '👩‍🎓', grade: '研一', major: '教育技术学', email: 'sunba@stu.edu.cn' },
  { id: 's7', name: '周九', avatar: '👨‍🎓', grade: '研二', major: '软件工程', email: 'zhoujiu@stu.edu.cn' },
  { id: 's8', name: '吴十', avatar: '👩‍🎓', grade: '研一', major: '计算机科学', email: 'wushi@stu.edu.cn' },
];

// 团队信息
export const teams = [
  {
    id: 'team1',
    name: 'AI教育创新组',
    projectId: 'p1',
    members: ['s1', 's2', 's3', 's4'],
    leader: 's1',
  },
  {
    id: 'team2',
    name: '智慧课堂组',
    projectId: 'p1',
    members: ['s5', 's6', 's7', 's8'],
    leader: 's5',
  },
];

// PBL项目
export const projects = [
  {
    id: 'p1',
    title: '基于AI的个性化学习系统设计',
    teacherId: 't1',
    subject: '教育技术学',
    grade: '研究生',
    status: 'active',
    startDate: '2026-03-01',
    endDate: '2026-05-30',
    description: '设计并原型开发一个基于人工智能技术的个性化学习推荐系统，探索AI在教育领域的应用潜力。',
    teams: ['team1', 'team2'],
    objectives: [
      '理解AI在教育中的应用场景与伦理边界',
      '掌握个性化学习系统的设计方法论',
      '培养团队协作与项目管理能力',
      '提升批判性思维与创新设计能力',
    ],
    phases: [
      { name: '需求分析', duration: '2周', status: 'completed' },
      { name: '方案设计', duration: '3周', status: 'active' },
      { name: '原型开发', duration: '3周', status: 'pending' },
      { name: '测试迭代', duration: '2周', status: 'pending' },
      { name: '成果展示', duration: '2周', status: 'pending' },
    ],
    rubric: {
      dimensions: [
        { name: '研究能力', weight: 20, description: '文献综述、需求调研的深度与广度' },
        { name: '设计能力', weight: 25, description: '方案设计的创新性、合理性与可行性' },
        { name: '技术实现', weight: 20, description: '原型开发的技术水平与完成度' },
        { name: '团队协作', weight: 20, description: '任务分工、沟通协调、冲突解决' },
        { name: '展示表达', weight: 15, description: '成果展示的逻辑性、表达力与说服力' },
      ],
    },
    crossDisciplinary: ['人工智能', '学习科学', '用户体验设计', '数据分析'],
  },
];

// 教学方案模板
export const teachingPlanTemplate = {
  projectBackground: `
    在当前数字化转型的教育背景下，人工智能技术正在深刻改变教与学的方式。
    本项目以"个性化学习"为核心主题，引导学生探索AI技术如何根据学习者的
    个体差异提供定制化的学习体验。项目设定在一个模拟的K-12学校场景中，
    学生需要为该校设计一套AI驱动的个性化学习推荐系统。
  `,
  learningObjectives: [
    { type: '知识目标', content: '掌握推荐算法基础原理与个性化学习理论' },
    { type: '能力目标', content: '能够独立完成需求分析、系统设计与原型开发' },
    { type: '素养目标', content: '培养批判性思维、协作能力与创新意识' },
  ],
  taskBreakdown: [
    {
      phase: '第一阶段：需求分析',
      tasks: ['文献综述与案例研究', '用户访谈与需求调研', '需求文档撰写'],
      duration: '第1-2周',
    },
    {
      phase: '第二阶段：方案设计',
      tasks: ['系统架构设计', '算法方案选型', '界面原型设计', '技术可行性评估'],
      duration: '第3-5周',
    },
    {
      phase: '第三阶段：原型开发',
      tasks: ['核心功能开发', '数据模型搭建', '前端界面实现'],
      duration: '第6-8周',
    },
    {
      phase: '第四阶段：测试迭代',
      tasks: ['用户测试', '问题修复', '功能优化'],
      duration: '第9-10周',
    },
    {
      phase: '第五阶段：成果展示',
      tasks: ['项目报告撰写', '演示文稿制作', '成果答辩展示'],
      duration: '第11-12周',
    },
  ],
};

// 任务数据
export const tasks = [
  // Team 1 的任务
  {
    id: 'task1',
    teamId: 'team1',
    projectId: 'p1',
    title: '文献综述：AI在教育中的应用现状',
    assignee: 's1',
    status: 'completed',
    priority: 'high',
    startDate: '2026-03-01',
    dueDate: '2026-03-10',
    completedDate: '2026-03-09',
    description: '收集并分析近5年内关于AI在教育领域应用的文献，撰写综述报告。',
  },
  {
    id: 'task2',
    teamId: 'team1',
    projectId: 'p1',
    title: '用户需求调研与访谈',
    assignee: 's2',
    status: 'completed',
    priority: 'high',
    startDate: '2026-03-05',
    dueDate: '2026-03-14',
    completedDate: '2026-03-13',
    description: '设计访谈提纲，对教师和学生进行用户调研，整理需求。',
  },
  {
    id: 'task3',
    teamId: 'team1',
    projectId: 'p1',
    title: '系统架构设计文档',
    assignee: 's3',
    status: 'in_progress',
    priority: 'high',
    startDate: '2026-03-15',
    dueDate: '2026-03-28',
    completedDate: null,
    description: '基于需求分析结果，设计系统整体架构方案。',
  },
  {
    id: 'task4',
    teamId: 'team1',
    projectId: 'p1',
    title: '推荐算法调研与选型',
    assignee: 's1',
    status: 'in_progress',
    priority: 'medium',
    startDate: '2026-03-15',
    dueDate: '2026-03-25',
    completedDate: null,
    description: '调研主流推荐算法，对比分析适合教育场景的方案。',
  },
  {
    id: 'task5',
    teamId: 'team1',
    projectId: 'p1',
    title: 'UI/UX原型设计',
    assignee: 's4',
    status: 'pending',
    priority: 'medium',
    startDate: '2026-03-20',
    dueDate: '2026-04-05',
    completedDate: null,
    description: '设计学习系统的界面原型，包括学生端和教师端。',
  },
  {
    id: 'task6',
    teamId: 'team1',
    projectId: 'p1',
    title: '核心推荐模块开发',
    assignee: 's3',
    status: 'pending',
    priority: 'high',
    startDate: '2026-04-01',
    dueDate: '2026-04-20',
    completedDate: null,
    description: '实现核心推荐算法模块的原型代码。',
  },
  // Team 2 的任务
  {
    id: 'task7',
    teamId: 'team2',
    projectId: 'p1',
    title: '智慧课堂技术调研',
    assignee: 's5',
    status: 'completed',
    priority: 'high',
    startDate: '2026-03-01',
    dueDate: '2026-03-12',
    completedDate: '2026-03-11',
    description: '调研现有智慧课堂技术方案与产品。',
  },
  {
    id: 'task8',
    teamId: 'team2',
    projectId: 'p1',
    title: '学习数据分析方案设计',
    assignee: 's6',
    status: 'in_progress',
    priority: 'high',
    startDate: '2026-03-15',
    dueDate: '2026-03-30',
    completedDate: null,
    description: '设计学习行为数据的采集与分析方案。',
  },
  {
    id: 'task9',
    teamId: 'team2',
    projectId: 'p1',
    title: '自适应学习路径算法研究',
    assignee: 's7',
    status: 'pending',
    priority: 'medium',
    startDate: '2026-03-25',
    dueDate: '2026-04-10',
    completedDate: null,
    description: '研究自适应学习路径推荐算法的理论基础。',
  },
  {
    id: 'task10',
    teamId: 'team2',
    projectId: 'p1',
    title: '前端界面原型开发',
    assignee: 's8',
    status: 'pending',
    priority: 'medium',
    startDate: '2026-04-01',
    dueDate: '2026-04-15',
    completedDate: null,
    description: '开发智慧课堂系统的前端交互原型。',
  },
];

// 过程数据 - 讨论记录
export const discussions = [
  {
    id: 'd1',
    teamId: 'team1',
    date: '2026-03-05',
    duration: 90,
    participants: ['s1', 's2', 's3', 's4'],
    summary: '讨论项目方向与分工',
    keyPoints: [
      '确定以K-12场景为切入点',
      '张三负责文献调研，李四负责用户访谈',
      '王五负责技术架构，赵六负责UI设计',
    ],
    tags: ['分工', '方向确定'],
  },
  {
    id: 'd2',
    teamId: 'team1',
    date: '2026-03-12',
    duration: 60,
    participants: ['s1', 's2', 's3'],
    summary: '需求分析结果汇报',
    keyPoints: [
      '文献综述发现协同过滤在教育场景效果有限',
      '用户访谈显示教师最关注学习进度可视化',
      '决定采用混合推荐策略',
    ],
    tags: ['需求分析', '技术选型'],
  },
  {
    id: 'd3',
    teamId: 'team1',
    date: '2026-03-19',
    duration: 75,
    participants: ['s1', 's2', 's3', 's4'],
    summary: '系统架构方案讨论',
    keyPoints: [
      '前后端分离架构方案获得一致认可',
      '数据库选型讨论：MySQL vs MongoDB',
      '赵六提出了优秀的交互设计思路',
    ],
    tags: ['架构设计', '技术讨论'],
  },
  {
    id: 'd4',
    teamId: 'team2',
    date: '2026-03-06',
    duration: 80,
    participants: ['s5', 's6', 's7', 's8'],
    summary: '项目启动与分工讨论',
    keyPoints: [
      '钱七负责技术调研总协调',
      '孙八负责数据分析方案',
      '周九负责算法研究',
      '吴十负责前端开发',
    ],
    tags: ['项目启动', '任务分配'],
  },
  {
    id: 'd5',
    teamId: 'team2',
    date: '2026-03-18',
    duration: 50,
    participants: ['s5', 's7', 's8'],
    summary: '技术方案中期讨论',
    keyPoints: [
      '调研发现几个成熟的自适应学习框架',
      '决定基于知识图谱构建学习路径',
      '注意：孙八未参加本次讨论',
    ],
    tags: ['技术方案', '中期检查'],
  },
];

// 文档版本历史
export const documents = [
  {
    id: 'doc1',
    teamId: 'team1',
    title: '需求分析报告',
    currentVersion: 'v3.0',
    versions: [
      { version: 'v1.0', author: 's1', date: '2026-03-08', changes: '初稿完成' },
      { version: 'v2.0', author: 's2', date: '2026-03-11', changes: '加入用户访谈数据' },
      { version: 'v3.0', author: 's1', date: '2026-03-14', changes: '根据讨论修改优化' },
    ],
  },
  {
    id: 'doc2',
    teamId: 'team1',
    title: '系统架构设计文档',
    currentVersion: 'v1.2',
    versions: [
      { version: 'v1.0', author: 's3', date: '2026-03-18', changes: '架构初稿' },
      { version: 'v1.1', author: 's3', date: '2026-03-20', changes: '添加数据库设计' },
      { version: 'v1.2', author: 's1', date: '2026-03-22', changes: '补充API设计部分' },
    ],
  },
  {
    id: 'doc3',
    teamId: 'team2',
    title: '智慧课堂技术调研报告',
    currentVersion: 'v2.0',
    versions: [
      { version: 'v1.0', author: 's5', date: '2026-03-10', changes: '初稿' },
      { version: 'v2.0', author: 's5', date: '2026-03-15', changes: '补充竞品分析' },
    ],
  },
];

// AI评估数据
export const evaluations = {
  team1: {
    teamId: 'team1',
    evaluationDate: '2026-03-25',
    overallScore: 82,
    members: [
      {
        studentId: 's1',
        name: '张三',
        scores: {
          research: 88, collaboration: 85, problemSolving: 80, communication: 82, innovation: 78,
        },
        overallScore: 83,
        contributions: [
          { type: 'document', count: 5, detail: '提交5份文档，包括文献综述和需求分析' },
          { type: 'discussion', count: 3, detail: '参与全部3次讨论，发言活跃' },
          { type: 'keyIdea', detail: '提出采用混合推荐策略的关键建议' },
        ],
        timeInvestment: { totalHours: 42, weeklyAvg: 10.5, trend: 'stable' },
        strengths: ['文献调研能力突出', '善于总结归纳', '主动承担核心任务'],
        weaknesses: ['技术实现能力有待提升', '有时沟通不够及时'],
        suggestions: ['建议加强编程实践', '可以更多与技术组成员交流'],
        anomaly: null,
      },
      {
        studentId: 's2',
        name: '李四',
        scores: {
          research: 75, collaboration: 90, problemSolving: 78, communication: 88, innovation: 72,
        },
        overallScore: 81,
        contributions: [
          { type: 'document', count: 3, detail: '提交3份文档，主要负责用户调研' },
          { type: 'discussion', count: 3, detail: '参与全部讨论，擅长总结发言' },
          { type: 'keyIdea', detail: '用户访谈设计方案获得教师好评' },
        ],
        timeInvestment: { totalHours: 38, weeklyAvg: 9.5, trend: 'increasing' },
        strengths: ['沟通协调能力强', '用户研究方法扎实', '团队氛围调节者'],
        weaknesses: ['技术文档撰写需加强', '研究深度可进一步提升'],
        suggestions: ['建议深入学习数据分析方法', '尝试参与技术实现环节'],
        anomaly: null,
      },
      {
        studentId: 's3',
        name: '王五',
        scores: {
          research: 82, collaboration: 75, problemSolving: 90, communication: 70, innovation: 85,
        },
        overallScore: 80,
        contributions: [
          { type: 'document', count: 4, detail: '提交架构设计文档及多次更新' },
          { type: 'discussion', count: 2, detail: '参与2次讨论，技术观点明确' },
          { type: 'keyIdea', detail: '前后端分离架构方案设计' },
        ],
        timeInvestment: { totalHours: 45, weeklyAvg: 11.2, trend: 'stable' },
        strengths: ['技术能力强', '架构设计思路清晰', '独立解决问题能力好'],
        weaknesses: ['团队沟通参与度偏低', '文档表达有时不够清晰'],
        suggestions: ['建议增加与组员的主动沟通', '可以尝试写更详细的技术文档'],
        anomaly: null,
      },
      {
        studentId: 's4',
        name: '赵六',
        scores: {
          research: 70, collaboration: 88, problemSolving: 72, communication: 85, innovation: 90,
        },
        overallScore: 81,
        contributions: [
          { type: 'document', count: 2, detail: '提交UI设计稿初版' },
          { type: 'discussion', count: 3, detail: '参与全部讨论，提出创意想法' },
          { type: 'keyIdea', detail: '创新的学习路径可视化设计方案' },
        ],
        timeInvestment: { totalHours: 35, weeklyAvg: 8.8, trend: 'increasing' },
        strengths: ['创新设计思维突出', '善于提出新颖想法', '协作意愿强'],
        weaknesses: ['研究方法论需加强', '任务完成效率可提升'],
        suggestions: ['建议系统学习UX研究方法', '制定更细致的个人工作计划'],
        anomaly: null,
      },
    ],
  },
  team2: {
    teamId: 'team2',
    evaluationDate: '2026-03-25',
    overallScore: 74,
    members: [
      {
        studentId: 's5',
        name: '钱七',
        scores: {
          research: 85, collaboration: 82, problemSolving: 80, communication: 78, innovation: 76,
        },
        overallScore: 80,
        contributions: [
          { type: 'document', count: 4, detail: '提交技术调研报告及更新' },
          { type: 'discussion', count: 2, detail: '参与2次讨论，主导技术方向' },
          { type: 'keyIdea', detail: '提出基于知识图谱的学习路径方案' },
        ],
        timeInvestment: { totalHours: 40, weeklyAvg: 10, trend: 'stable' },
        strengths: ['技术调研能力强', '团队领导力好', '方向把控准确'],
        weaknesses: ['有时过于关注技术细节', '需要更多关注团队成员状态'],
        suggestions: ['建议定期检查团队成员进展', '适当分配更多指导时间'],
        anomaly: null,
      },
      {
        studentId: 's6',
        name: '孙八',
        scores: {
          research: 60, collaboration: 55, problemSolving: 58, communication: 50, innovation: 55,
        },
        overallScore: 56,
        contributions: [
          { type: 'document', count: 1, detail: '提交1份初步的数据分析方案' },
          { type: 'discussion', count: 1, detail: '仅参与1次讨论，缺席中期讨论' },
          { type: 'keyIdea', detail: '暂无突出贡献记录' },
        ],
        timeInvestment: { totalHours: 15, weeklyAvg: 3.8, trend: 'decreasing' },
        strengths: ['具备基础数据分析知识'],
        weaknesses: ['参与度明显不足', '讨论缺席', '任务推进缓慢'],
        suggestions: ['建议与组长沟通困难并寻求帮助', '制定每日小目标提升参与感'],
        anomaly: {
          type: 'low_participation',
          severity: 'high',
          description: '该成员参与度低于团队平均水平50%以上，讨论缺席率高，需要教师关注介入。',
        },
      },
      {
        studentId: 's7',
        name: '周九',
        scores: {
          research: 78, collaboration: 72, problemSolving: 82, communication: 68, innovation: 80,
        },
        overallScore: 76,
        contributions: [
          { type: 'document', count: 2, detail: '提交算法调研笔记' },
          { type: 'discussion', count: 2, detail: '参与2次讨论' },
          { type: 'keyIdea', detail: '提出知识图谱构建的技术路线' },
        ],
        timeInvestment: { totalHours: 32, weeklyAvg: 8, trend: 'stable' },
        strengths: ['算法理解能力好', '技术研究扎实'],
        weaknesses: ['主动沟通较少', '需要更多团队配合'],
        suggestions: ['建议增加与团队的交流频率', '尝试将研究成果更好地呈现给团队'],
        anomaly: null,
      },
      {
        studentId: 's8',
        name: '吴十',
        scores: {
          research: 72, collaboration: 78, problemSolving: 75, communication: 80, innovation: 70,
        },
        overallScore: 75,
        contributions: [
          { type: 'document', count: 2, detail: '提交前端技术调研和设计思路' },
          { type: 'discussion', count: 2, detail: '参与2次讨论' },
          { type: 'keyIdea', detail: '无特别突出贡献' },
        ],
        timeInvestment: { totalHours: 28, weeklyAvg: 7, trend: 'stable' },
        strengths: ['前端开发基础好', '沟通表达清晰'],
        weaknesses: ['创新思维有待提升', '需要更多独立思考'],
        suggestions: ['建议多学习优秀的交互设计案例', '尝试提出自己的设计方案'],
        anomaly: null,
      },
    ],
  },
};

// 教师决策支持 - 系统告警与建议
export const alerts = [
  {
    id: 'alert1',
    type: 'low_participation',
    severity: 'high',
    teamId: 'team2',
    studentId: 's6',
    studentName: '孙八',
    title: '成员参与度异常偏低',
    description: '孙八近两周参与度持续下降，讨论出席率50%，任务完成进度落后于计划。',
    suggestion: '建议与该学生进行一对一沟通，了解是否遇到困难或需要调整任务分配。',
    timestamp: '2026-03-24',
    resolved: false,
  },
  {
    id: 'alert2',
    type: 'progress_delay',
    severity: 'medium',
    teamId: 'team2',
    studentId: null,
    title: '团队2整体进度滞后',
    description: '智慧课堂组当前进度落后预期约1周，主要原因是数据分析方案推进缓慢。',
    suggestion: '建议检查团队任务分配是否合理，考虑重新分配部分任务给其他成员。',
    timestamp: '2026-03-23',
    resolved: false,
  },
  {
    id: 'alert3',
    type: 'collaboration_issue',
    severity: 'low',
    teamId: 'team1',
    studentId: 's3',
    studentName: '王五',
    title: '成员沟通参与度偏低',
    description: '王五虽然技术贡献突出，但在团队讨论中发言较少，与其他成员的互动偏低。',
    suggestion: '建议鼓励该学生在讨论中更多分享技术想法，可安排其进行技术分享环节。',
    timestamp: '2026-03-22',
    resolved: false,
  },
];

// 协作行为数据 - 用于可视化
export const collaborationData = {
  team1: {
    interactions: [
      { from: 's1', to: 's2', weight: 8, type: '讨论' },
      { from: 's1', to: 's3', weight: 6, type: '文档协作' },
      { from: 's1', to: 's4', weight: 4, type: '讨论' },
      { from: 's2', to: 's3', weight: 3, type: '讨论' },
      { from: 's2', to: 's4', weight: 5, type: '讨论' },
      { from: 's3', to: 's4', weight: 2, type: '技术交流' },
    ],
    weeklyActivity: [
      { week: '第1周', s1: 12, s2: 10, s3: 11, s4: 8 },
      { week: '第2周', s1: 10, s2: 11, s3: 12, s4: 9 },
      { week: '第3周', s1: 11, s2: 9, s3: 13, s4: 10 },
      { week: '第4周', s1: 9, s2: 8, s3: 9, s4: 8 },
    ],
  },
  team2: {
    interactions: [
      { from: 's5', to: 's6', weight: 3, type: '讨论' },
      { from: 's5', to: 's7', weight: 7, type: '技术交流' },
      { from: 's5', to: 's8', weight: 5, type: '讨论' },
      { from: 's6', to: 's7', weight: 1, type: '讨论' },
      { from: 's6', to: 's8', weight: 1, type: '讨论' },
      { from: 's7', to: 's8', weight: 4, type: '技术交流' },
    ],
    weeklyActivity: [
      { week: '第1周', s5: 11, s6: 7, s7: 9, s8: 8 },
      { week: '第2周', s5: 10, s6: 5, s7: 8, s8: 7 },
      { week: '第3周', s5: 10, s6: 3, s7: 9, s8: 7 },
      { week: '第4周', s5: 9, s6: 0, s7: 6, s8: 6 },
    ],
  },
};

// 能力维度定义
export const abilityDimensions = [
  { key: 'research', label: '研究能力', fullMark: 100 },
  { key: 'collaboration', label: '协作能力', fullMark: 100 },
  { key: 'problemSolving', label: '问题解决', fullMark: 100 },
  { key: 'communication', label: '沟通表达', fullMark: 100 },
  { key: 'innovation', label: '创新能力', fullMark: 100 },
];
