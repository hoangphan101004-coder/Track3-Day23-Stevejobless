# WORKLOG NHÓM 2 NGƯỜI

## 1. Thông tin chung

- Tên bài: Day 23 — Track 3 — LangGraph Agentic Orchestration
- Tên nhóm: ______________________________________________
- Lớp/nhóm học phần: _____________________________________
- Repository: _____________________________________________
- Nhánh làm việc: _________________________________________
- Thời gian bắt đầu: ______________________________________
- Thời gian hoàn thành: ___________________________________

### Thành viên 1

- Họ và tên: ______________________________________________
- Mã sinh viên: ___________________________________________
- Email: __________________________________________________
- GitHub: __________________________________________________

### Thành viên 2

- Họ và tên: ______________________________________________
- Mã sinh viên: ___________________________________________
- Email: __________________________________________________
- GitHub: __________________________________________________

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

Đầu ra/evidence của thành viên 1:

- Commit/link: _____________________________________________
- Test command: ____________________________________________
- Test result: _____________________________________________
- Evidence khác: ___________________________________________
- Vấn đề hoặc giới hạn còn lại: _____________________________

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

Đầu ra/evidence của thành viên 2:

- Commit/link: _____________________________________________
- Test command: ____________________________________________
- Test result: _____________________________________________
- Evidence khác: ___________________________________________
- Vấn đề hoặc giới hạn còn lại: _____________________________

## 5. Nhật ký làm việc

Sao chép khối dưới đây cho mỗi phiên làm việc.

### Phiên làm việc số: ______

- Ngày: ____________________________________________________
- Thời gian bắt đầu: _______________________________________
- Thời gian kết thúc: ______________________________________
- Người thực hiện: _________________________________________
- Hạng mục thực hiện: ______________________________________
- File đã thay đổi: ________________________________________
- Nội dung đã hoàn thành: __________________________________
- Lệnh kiểm tra đã chạy: ___________________________________
- Kết quả kiểm tra: ________________________________________
- Commit/PR/link evidence: __________________________________
- Vấn đề gặp phải: _________________________________________
- Cách xử lý: ______________________________________________
- Công việc tiếp theo: _____________________________________

## 6. Checkpoint review chéo

### Review của thành viên 1 cho phần thành viên 2

- Ngày review: _____________________________________________
- Phạm vi review: __________________________________________
- Kết quả: _________________________________________________
- Lỗi hoặc góp ý: __________________________________________
- Trạng thái xử lý góp ý: __________________________________
- Link commit/evidence sau sửa: _____________________________

### Review của thành viên 2 cho phần thành viên 1

- Ngày review: _____________________________________________
- Phạm vi review: __________________________________________
- Kết quả: _________________________________________________
- Lỗi hoặc góp ý: __________________________________________
- Trạng thái xử lý góp ý: __________________________________
- Link commit/evidence sau sửa: _____________________________

## 7. Gate cuối của cả nhóm

- [ ] `python -m ruff check src tests` pass.
- [ ] `python -m mypy src` pass.
- [ ] `python -m pytest -q` pass và không còn E2E test bị skip khi API key đã cấu hình.
- [ ] Chạy đủ 7 sample scenarios bằng implementation tổng quát.
- [ ] `outputs/metrics.json` validation pass.
- [ ] Retry hữu hạn và S07 đi vào dead-letter đúng boundary.
- [ ] Approved action chỉ chạy tool sau approval.
- [ ] Rejected action đi clarification và không gọi tool.
- [ ] Mọi route có terminal event `finalize`.
- [ ] Persistence evidence gắn đúng thread ID.
- [ ] Báo cáo khớp với metrics và evidence mới nhất.
- [ ] Có ít nhất hai failure mode trong báo cáo.
- [ ] Không có secret hoặc hidden grading data trong bài nộp.
- [ ] `git diff --check` pass.

Kết quả gate cuối:

- Ngày chạy: _______________________________________________
- Người chạy: ______________________________________________
- Tổng số test pass: _______________________________________
- Scenario success rate: ___________________________________
- Metrics validation: ______________________________________
- Lint/typecheck: ___________________________________________
- Commit cuối: _____________________________________________
- Link bài nộp: ____________________________________________

## 8. Xác nhận đóng góp

### Thành viên 1

- Tôi xác nhận phần đóng góp và evidence nêu trên là chính xác.
- Họ tên: __________________________________________________
- Ngày xác nhận: ___________________________________________
- Chữ ký/xác nhận điện tử: _________________________________

### Thành viên 2

- Tôi xác nhận phần đóng góp và evidence nêu trên là chính xác.
- Họ tên: __________________________________________________
- Ngày xác nhận: ___________________________________________
- Chữ ký/xác nhận điện tử: _________________________________
