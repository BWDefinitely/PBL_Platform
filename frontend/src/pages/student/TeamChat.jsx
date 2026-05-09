import { useState, useRef, useEffect } from 'react';
import { students, teams } from '../../data/mockData';

const currentStudent = students[0]; // 张三 s1
const team = teams.find(t => t.members.includes(currentStudent.id));
const teamMembers = team.members.map(id => students.find(s => s.id === id));

// 模拟历史聊天记录
const initialMessages = [
  { id: 1, sender: 's1', content: '大家好，今天下午的讨论主要聚焦系统架构方案，请大家准备一下各自的想法。', time: '14:00', type: 'text' },
  { id: 2, sender: 's2', content: '好的，我整理了用户调研中关于功能需求的部分，待会可以分享。', time: '14:02', type: 'text' },
  { id: 3, sender: 's3', content: '我这边有两个架构方案的对比，前后端分离 vs 单体应用，稍后详细说明。', time: '14:03', type: 'text' },
  { id: 4, sender: 's4', content: '我研究了几个竞品的UI设计，有些交互模式值得借鉴。', time: '14:05', type: 'text' },
  { id: 5, sender: 's1', content: '那我们开始吧。首先王五介绍一下两个架构方案？', time: '14:06', type: 'text' },
  { id: 6, sender: 's3', content: '前后端分离方案：前端React + 后端Spring Boot + MySQL。优点是团队可并行开发，缺点是初期搭建成本较高。单体方案搭建快但后期维护困难。我建议前后端分离。', time: '14:08', type: 'text' },
  { id: 7, sender: 's2', content: '从用户调研来看，教师最看重的是学习进度可视化和数据统计分析功能，前后端分离更适合做复杂的数据展示。', time: '14:12', type: 'text' },
  { id: 8, sender: 's4', content: '我也倾向前后端分离，这样前端可以做更丰富的交互效果。另外我发现学习路径的可视化可以参考知识图谱的方式来呈现。', time: '14:15', type: 'text' },
  { id: 9, sender: 's1', content: '好的，那架构方案就确定前后端分离。接下来讨论数据库选型，MySQL 还是 MongoDB？', time: '14:18', type: 'text' },
  { id: 10, sender: 's3', content: '学习数据结构比较灵活，MongoDB在处理半结构化数据上更有优势。但如果需要复杂查询和事务支持，MySQL更稳定。', time: '14:20', type: 'text' },
  { id: 11, sender: 's2', content: '从需求来看，用户数据、课程数据是结构化的，但学习行为日志是半结构化的，可以考虑混合使用。', time: '14:23', type: 'text' },
  { id: 12, sender: 's1', content: '混合方案成本会不会太高？我们时间有限，建议主库用MySQL，学习行为日志后期再考虑。', time: '14:25', type: 'text' },
  { id: 13, sender: 's4', content: '赞同，先用MySQL保证功能完整性，后续可以平滑迁移。', time: '14:27', type: 'text' },
  { id: 14, sender: 's3', content: '可以接受。那API设计部分我来负责，张三你来补充推荐算法的接口需求。', time: '14:30', type: 'text' },
  { id: 15, sender: 's1', content: '没问题。那今天的讨论差不多了，总结一下：1) 采用前后端分离架构；2) 数据库选MySQL；3) 赵六继续细化UI设计；4) 下周开始进入原型开发。大家还有什么要补充的吗？', time: '14:35', type: 'text' },
  { id: 16, sender: 's2', content: '我建议下次讨论前大家各自把负责模块的技术方案写一个简单文档，这样讨论效率会更高。', time: '14:37', type: 'text' },
  { id: 17, sender: 's1', content: '好主意！那就这样，大家辛苦了！', time: '14:38', type: 'text' },
];

// AI会议纪要模板
const aiMeetingSummary = {
  title: '系统架构方案讨论会议纪要',
  date: '2026-03-19 14:00 - 14:38',
  participants: ['张三', '李四', '王五', '赵六'],
  duration: '38分钟',
  keyDecisions: [
    '确定采用前后端分离架构方案（前端React + 后端Spring Boot + MySQL）',
    '数据库选型确定为MySQL，学习行为日志后续再考虑NoSQL方案',
    '赵六继续细化UI/UX设计，参考知识图谱方式呈现学习路径',
    '下周正式进入原型开发阶段',
  ],
  keyDiscussions: [
    {
      topic: '架构方案选型',
      summary: '王五对比了前后端分离与单体应用两种方案。团队一致认为前后端分离更利于并行开发和复杂数据展示，决定采纳该方案。',
    },
    {
      topic: '数据库选型',
      summary: '讨论了MySQL与MongoDB的优劣。考虑到时间成本和功能优先级，决定主库使用MySQL，学习行为日志的NoSQL方案后期再考虑。',
    },
    {
      topic: 'UI设计方向',
      summary: '赵六分享了竞品调研中发现的交互模式，提出学习路径可视化采用知识图谱呈现方式，获得团队认可。',
    },
  ],
  actionItems: [
    { assignee: '王五', task: '完成API设计文档', deadline: '下周三' },
    { assignee: '张三', task: '补充推荐算法接口需求', deadline: '下周三' },
    { assignee: '赵六', task: '细化UI/UX设计稿', deadline: '下周五' },
    { assignee: '全体成员', task: '各自编写负责模块的技术方案简要文档', deadline: '下次讨论前' },
  ],
  memberContributions: [
    { name: '张三', role: '会议主持，推动议程进展，做出最终总结', messages: 6 },
    { name: '李四', role: '提供用户调研数据支撑决策，提出流程优化建议', messages: 3 },
    { name: '王五', role: '提供核心技术方案对比分析，主导架构讨论', messages: 3 },
    { name: '赵六', role: '分享竞品UI调研结果，提出创新可视化方案', messages: 2 },
  ],
};

export default function TeamChat() {
  const [messages, setMessages] = useState(initialMessages);
  const [input, setInput] = useState('');
  const [meetingActive, setMeetingActive] = useState(false);
  const [showSummary, setShowSummary] = useState(false);
  const [generatingSummary, setGeneratingSummary] = useState(false);
  const messagesEndRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const getSenderInfo = (id) => {
    if (id === 'ai') return { name: 'AI助手', avatar: '🤖' };
    const s = students.find(s => s.id === id);
    return s ? { name: s.name, avatar: s.avatar } : { name: '未知', avatar: '❓' };
  };

  const handleSend = () => {
    if (!input.trim()) return;
    const newMsg = {
      id: messages.length + 1,
      sender: currentStudent.id,
      content: input,
      time: new Date().toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' }),
      type: 'text',
    };
    setMessages([...messages, newMsg]);
    setInput('');
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const startMeeting = () => {
    setMeetingActive(true);
    setShowSummary(false);
    const aiMsg = {
      id: messages.length + 1,
      sender: 'ai',
      content: '📋 会议模式已开启！我会在会议期间记录大家的讨论内容。会议结束后，我将自动生成会议纪要。请大家开始讨论吧～',
      time: new Date().toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' }),
      type: 'system',
    };
    setMessages(prev => [...prev, aiMsg]);
  };

  const endMeeting = () => {
    setMeetingActive(false);
    setGeneratingSummary(true);

    const processingMsg = {
      id: messages.length + 1,
      sender: 'ai',
      content: '⏳ 会议已结束，正在分析聊天记录并生成会议纪要...',
      time: new Date().toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' }),
      type: 'system',
    };
    setMessages(prev => [...prev, processingMsg]);

    setTimeout(() => {
      setGeneratingSummary(false);
      setShowSummary(true);
      const summaryMsg = {
        id: messages.length + 2,
        sender: 'ai',
        content: 'AI_SUMMARY',
        time: new Date().toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' }),
        type: 'summary',
      };
      setMessages(prev => [...prev, summaryMsg]);
    }, 3000);
  };

  const renderSummaryCard = () => (
    <div style={{ background: 'linear-gradient(135deg, var(--primary-50), #F0FDF4)', borderRadius: 'var(--radius)', padding: 20, maxWidth: 560 }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 16 }}>
        <span style={{ fontSize: 20 }}>📋</span>
        <span style={{ fontSize: 16, fontWeight: 700, color: 'var(--text)' }}>{aiMeetingSummary.title}</span>
      </div>

      <div style={{ fontSize: 12, color: 'var(--text-muted)', marginBottom: 16, display: 'flex', gap: 16 }}>
        <span>🕐 {aiMeetingSummary.date}</span>
        <span>⏱ {aiMeetingSummary.duration}</span>
        <span>👥 {aiMeetingSummary.participants.join('、')}</span>
      </div>

      <div style={{ marginBottom: 14 }}>
        <div style={{ fontSize: 13, fontWeight: 700, color: 'var(--primary)', marginBottom: 8 }}>✅ 关键决议</div>
        {aiMeetingSummary.keyDecisions.map((d, i) => (
          <div key={i} style={{ fontSize: 13, color: 'var(--text-secondary)', paddingLeft: 12, marginBottom: 4, display: 'flex', gap: 6 }}>
            <span style={{ color: 'var(--secondary)' }}>•</span> {d}
          </div>
        ))}
      </div>

      <div style={{ marginBottom: 14 }}>
        <div style={{ fontSize: 13, fontWeight: 700, color: 'var(--primary)', marginBottom: 8 }}>💬 议题摘要</div>
        {aiMeetingSummary.keyDiscussions.map((d, i) => (
          <div key={i} style={{ fontSize: 13, marginBottom: 8, padding: '8px 12px', background: 'white', borderRadius: 'var(--radius-sm)', border: '1px solid var(--border-light)' }}>
            <div style={{ fontWeight: 600, color: 'var(--text)', marginBottom: 2 }}>{d.topic}</div>
            <div style={{ color: 'var(--text-secondary)' }}>{d.summary}</div>
          </div>
        ))}
      </div>

      <div style={{ marginBottom: 14 }}>
        <div style={{ fontSize: 13, fontWeight: 700, color: 'var(--primary)', marginBottom: 8 }}>📌 待办事项</div>
        <table style={{ width: '100%', fontSize: 12, background: 'white', borderRadius: 'var(--radius-sm)', overflow: 'hidden' }}>
          <thead>
            <tr style={{ background: 'var(--bg)' }}>
              <th style={{ padding: '8px 10px', textTransform: 'none', letterSpacing: 0, borderBottom: '1px solid var(--border-light)' }}>负责人</th>
              <th style={{ padding: '8px 10px', textTransform: 'none', letterSpacing: 0, borderBottom: '1px solid var(--border-light)' }}>任务</th>
              <th style={{ padding: '8px 10px', textTransform: 'none', letterSpacing: 0, borderBottom: '1px solid var(--border-light)' }}>截止</th>
            </tr>
          </thead>
          <tbody>
            {aiMeetingSummary.actionItems.map((a, i) => (
              <tr key={i}>
                <td style={{ padding: '6px 10px', fontWeight: 600, borderBottom: '1px solid var(--border-light)' }}>{a.assignee}</td>
                <td style={{ padding: '6px 10px', color: 'var(--text-secondary)', borderBottom: '1px solid var(--border-light)' }}>{a.task}</td>
                <td style={{ padding: '6px 10px', color: 'var(--text-muted)', borderBottom: '1px solid var(--border-light)' }}>{a.deadline}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <div>
        <div style={{ fontSize: 13, fontWeight: 700, color: 'var(--primary)', marginBottom: 8 }}>👥 成员参与度</div>
        {aiMeetingSummary.memberContributions.map((m, i) => (
          <div key={i} style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 6, fontSize: 12 }}>
            <span style={{ fontWeight: 600, width: 40 }}>{m.name}</span>
            <div style={{ flex: 1, height: 6, background: 'var(--border)', borderRadius: 3, overflow: 'hidden' }}>
              <div style={{ height: '100%', width: `${(m.messages / 6) * 100}%`, background: 'var(--primary)', borderRadius: 3 }} />
            </div>
            <span style={{ color: 'var(--text-muted)', width: 50 }}>{m.messages}条发言</span>
          </div>
        ))}
      </div>
    </div>
  );

  return (
    <div className="fade-in" style={{ display: 'flex', flexDirection: 'column', height: 'calc(100vh - 64px)' }}>
      <div className="page-header" style={{ marginBottom: 16 }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <div>
            <div className="page-title">💬 团队讨论</div>
            <div className="page-subtitle">{team.name} · {teamMembers.length}位成员 + AI助手</div>
          </div>
          <div style={{ display: 'flex', gap: 10 }}>
            {!meetingActive ? (
              <button className="btn btn-primary" onClick={startMeeting}>
                📋 开启会议模式
              </button>
            ) : (
              <button className="btn btn-success" onClick={endMeeting} disabled={generatingSummary}>
                {generatingSummary ? '⏳ 生成中...' : '✅ 结束会议 & 生成纪要'}
              </button>
            )}
          </div>
        </div>
      </div>

      {/* 在线成员栏 */}
      <div style={{ display: 'flex', gap: 6, marginBottom: 12, padding: '10px 16px', background: 'var(--card)', borderRadius: 'var(--radius-sm)', border: '1px solid var(--border)', alignItems: 'center' }}>
        <span style={{ fontSize: 12, color: 'var(--text-muted)', marginRight: 8 }}>在线：</span>
        {teamMembers.map(m => (
          <div key={m.id} style={{ display: 'flex', alignItems: 'center', gap: 4, padding: '4px 10px', background: 'var(--bg)', borderRadius: 16, fontSize: 12 }}>
            <span>{m.avatar}</span>
            <span style={{ fontWeight: 500 }}>{m.name}</span>
            {m.id === currentStudent.id && <span style={{ color: 'var(--secondary)', fontSize: 10 }}>（我）</span>}
          </div>
        ))}
        <div style={{ display: 'flex', alignItems: 'center', gap: 4, padding: '4px 10px', background: 'linear-gradient(135deg, var(--primary-50), #F0FDF4)', borderRadius: 16, fontSize: 12 }}>
          <span>🤖</span>
          <span style={{ fontWeight: 500 }}>AI助手</span>
        </div>
        {meetingActive && (
          <div style={{ marginLeft: 'auto', display: 'flex', alignItems: 'center', gap: 6 }}>
            <span style={{ width: 8, height: 8, borderRadius: '50%', background: 'var(--danger)' }} className="pulse" />
            <span style={{ fontSize: 12, fontWeight: 600, color: 'var(--danger)' }}>会议进行中</span>
          </div>
        )}
      </div>

      {/* 消息列表 */}
      <div style={{
        flex: 1,
        overflowY: 'auto',
        padding: '16px',
        background: 'var(--card)',
        borderRadius: 'var(--radius)',
        border: '1px solid var(--border)',
        marginBottom: 12,
      }}>
        {messages.map(msg => {
          const sender = getSenderInfo(msg.sender);
          const isMe = msg.sender === currentStudent.id;
          const isAI = msg.sender === 'ai';

          if (msg.type === 'summary') {
            return (
              <div key={msg.id} style={{ display: 'flex', gap: 10, marginBottom: 16, justifyContent: 'flex-start' }}>
                <div style={{ width: 36, height: 36, borderRadius: '50%', background: 'linear-gradient(135deg, var(--primary-50), #F0FDF4)', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: 18, flexShrink: 0 }}>🤖</div>
                <div style={{ maxWidth: '80%' }}>
                  <div style={{ fontSize: 12, color: 'var(--text-muted)', marginBottom: 4 }}>
                    AI助手 · {msg.time}
                  </div>
                  {renderSummaryCard()}
                </div>
              </div>
            );
          }

          return (
            <div key={msg.id} style={{
              display: 'flex',
              gap: 10,
              marginBottom: 14,
              flexDirection: isMe ? 'row-reverse' : 'row',
            }}>
              <div style={{
                width: 36, height: 36, borderRadius: '50%',
                background: isAI ? 'linear-gradient(135deg, var(--primary-50), #F0FDF4)' : isMe ? 'var(--primary-50)' : 'var(--bg)',
                display: 'flex', alignItems: 'center', justifyContent: 'center',
                fontSize: 18, flexShrink: 0,
                border: isAI ? '1px solid var(--primary-light)' : '1px solid var(--border)',
              }}>
                {sender.avatar}
              </div>
              <div style={{ maxWidth: '70%' }}>
                <div style={{ fontSize: 12, color: 'var(--text-muted)', marginBottom: 3, textAlign: isMe ? 'right' : 'left' }}>
                  {sender.name} · {msg.time}
                </div>
                <div style={{
                  padding: '10px 14px',
                  borderRadius: isMe ? '14px 4px 14px 14px' : '4px 14px 14px 14px',
                  background: isAI
                    ? 'linear-gradient(135deg, var(--primary-50), #F0FDF4)'
                    : isMe ? 'var(--primary)' : 'var(--bg)',
                  color: isMe && !isAI ? 'white' : 'var(--text)',
                  fontSize: 14,
                  lineHeight: 1.6,
                  border: isAI ? '1px solid var(--primary-light)' : 'none',
                }}>
                  {msg.content}
                </div>
              </div>
            </div>
          );
        })}
        <div ref={messagesEndRef} />
      </div>

      {/* 输入框 */}
      <div style={{
        display: 'flex',
        gap: 10,
        padding: '12px 16px',
        background: 'var(--card)',
        borderRadius: 'var(--radius)',
        border: '1px solid var(--border)',
      }}>
        <input
          className="form-input"
          style={{ flex: 1, border: 'none', boxShadow: 'none', padding: '8px 0' }}
          placeholder="输入消息... (Enter发送)"
          value={input}
          onChange={e => setInput(e.target.value)}
          onKeyDown={handleKeyDown}
        />
        <button className="btn btn-primary btn-sm" onClick={handleSend}>
          发送
        </button>
      </div>
    </div>
  );
}
