# 评审清单模板（Review Gate Checklist）

> 项目：A股基金量化选基工具（评审会版本）
> 日期：____-__-__
> 版本：________

## Gate-DOC：文档评审（产品 / 量化 / 工程）

### 产品负责人检查项
- [ ] PRD范围清晰：MVP只包含首页/选基/详情/对比/观察池
- [ ] 推荐解释模板完整：加分项、扣分项、风险提示、适用前提
- [ ] 免责声明位置明确且可见
- [ ] 评审结论：通过 / 驳回
- 签字：________

### 量化负责人检查项
- [ ] Base因子与Policy Overlay定义一致
- [ ] 权重模板（保守/均衡/进取）符合约束（Overlay<=25%）
- [ ] 未来函数防护规则明确（发布时间/生效时间/观测时间）
- [ ] 回测口径定义可复现
- [ ] 评审结论：通过 / 驳回
- 签字：________

### 工程负责人检查项
- [ ] API-SPEC与PRD字段一致
- [ ] 测试策略与CI门禁一致
- [ ] 非功能要求有可执行验证路径
- [ ] 评审结论：通过 / 驳回
- 签字：________

---

## Gate-CODE：代码评审

### 后端（Python/FastAPI）
- [ ] 评分公式实现与ADR一致
- [ ] 政策时间戳校验接口可用
- [ ] 单元测试覆盖率 >= 90%
- [ ] 集成测试全部通过
- 签字（后端）：________
- 签字（量化）：________

### 前端（React/Vite）
- [ ] 五页信息架构与原型一致
- [ ] 风险偏好切换可影响展示结果
- [ ] 推荐解释、公式说明、免责声明可见
- [ ] 单元测试覆盖率达标（lines/statements >=90，functions/branches >=80）
- 签字（前端）：________
- 签字（产品）：________

---

## Gate-RELEASE：发布门禁
- [ ] lint / type-check / unit / integration 全绿
- [ ] 前端验证：`cd /home/jerry/projects/fund-quant-web-docs/frontend && npm run check && npm run test:coverage`
- [ ] 后端验证：`cd /home/jerry/projects/fund-quant-web-docs/backend && ../.venv/bin/python -m pytest --cov=app --cov-report=term-missing --cov-fail-under=90 && ../.venv/bin/python -m pytest tests/test_integration.py -q`
- [ ] 人工走查完成（关键链路5条）
- [ ] 版本说明已记录变更与风险
- [ ] 上线审批：通过 / 驳回
- 签字（Owner）：________
