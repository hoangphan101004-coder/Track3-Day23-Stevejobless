# WORKLOG NHÓM 2 NGƯỜI

## 1. Thông tin chung

- Tên bài: Day 23 — Track 3 — LangGraph Agentic Orchestration
- Tên nhóm: Steve Jobless


### Thành viên 1

- Họ và tên:Phan Huy Hoang
- Mã sinh viên: 2A202601990

### Thành viên 2

- Họ và tên: Trần An Thắng
- Mã sinh viên: 2A202601756


## 2. Nguyên tắc phối hợp

- Mỗi thành viên chịu trách nhiệm chính cho một nhóm hạng mục, nhưng phải review chéo phần của người còn lại.
- Không sửa public tests, sample scenarios hoặc hidden grading boundary để che lỗi implementation.
- Không commit `.env`, API key, checkpoint database hoặc dữ liệu nhạy cảm.
- Mỗi hạng mục chỉ được đánh dấu hoàn thành khi có code, test và evidence tương ứng.
- Trước khi nộp, cả hai thành viên cùng chạy gate cuối và xác nhận báo cáo khớp với artifacts.

## 3. Phân công thành viên 1

Vai trò chính: **State, LLM và node behavior**

- [ ] Đọc target graph, rubric và contract của starter repository.
- [ ] Hoàn thiện `src/langgraph_agent_lab/state.py`:
  - [ ] Kiểm tra typed state và tính serializable.
  - [ ] Bổ sung `evaluation_result`, `pending_question`, `proposed_action`, `approval`.
  - [ ] Xác định đúng field append-only và field overwrite.
- [ ] Hoàn thiện `src/langgraph_agent_lab/llm.py`:
  - [ ] Chọn một LLM provider.
  - [ ] Nạp `.env` an toàn.
  - [ ] Kiểm tra model/package tương ứng.
- [ ] Hoàn thiện `src/langgraph_agent_lab/nodes.py`:
  - [ ] `intake_node`.
  - [ ] `classify_node` bằng LLM structured output.
  - [ ] `tool_node` và mô phỏng lỗi.
  - [ ] `evaluate_node` và quality gate.
  - [ ] `answer_node` bằng LLM grounded generation.
  - [ ] `ask_clarification_node`.
  - [ ] `risky_action_node`.
  - [ ] `approval_node`.
  - [ ] `retry_or_fallback_node`.
  - [ ] `dead_letter_node`.
  - [ ] `finalize_node`.
- [ ] Viết hoặc bổ sung test cho node behavior, approval boundary và dead-letter boundary.
- [ ] Review chéo routing, graph wiring và persistence do thành viên 2 thực hiện.



## 4. Phân công thành viên 2

Vai trò chính: **Routing, graph, persistence, metrics và báo cáo**

- [ ] Hoàn thiện `src/langgraph_agent_lab/routing.py`:
  - [ ] `route_after_classify`.
  - [ ] `route_after_evaluate`.
  - [ ] `route_after_retry`.
  - [ ] `route_after_approval`.
- [ ] Hoàn thiện `src/langgraph_agent_lab/graph.py`:
  - [ ] Đăng ký đủ 11 node.
  - [ ] Nối đủ fixed edges.
  - [ ] Nối 4 conditional edges.
  - [ ] Compile bằng checkpointer được truyền vào.
  - [ ] Bảo đảm mọi route đi qua `finalize → END`.
- [ ] Hoàn thiện `src/langgraph_agent_lab/persistence.py`:
  - [ ] Memory checkpointer cho test.
  - [ ] SQLite checkpointer và WAL.
  - [ ] Thread ID riêng cho mỗi scenario.
  - [ ] State history hoặc state read-back evidence.
- [ ] Hoàn thiện scenario runner và metrics:
  - [ ] Chạy đủ 7 sample scenarios.
  - [ ] Đo latency thực tế.
  - [ ] Ghi retry, approval visit, error và node visit.
  - [ ] Sinh `outputs/metrics.json`.
  - [ ] Sinh `outputs/persistence_evidence.json`.
- [ ] Hoàn thiện `src/langgraph_agent_lab/report.py` và `reports/lab_report.md`.
- [ ] Xuất Mermaid graph tại `outputs/graph.mmd`.
- [ ] Review chéo state, LLM integration và node behavior do thành viên 1 thực hiện.



