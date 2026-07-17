import contextlib
import importlib.util
import io
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path


MODULE_PATH = Path(__file__).resolve().parents[1] / "tools" / "knowledge_governance.py"
SPEC = importlib.util.spec_from_file_location("knowledge_governance", MODULE_PATH)
governance = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(governance)


class KnowledgeGovernanceTest(unittest.TestCase):
    def setUp(self):
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.repo = Path(self.temporary_directory.name)
        (self.repo / "knowledge-catalog.md").write_text(
            "# 测试知识库\n", encoding="utf-8"
        )

    def tearDown(self):
        self.temporary_directory.cleanup()

    def run_command(self, *arguments):
        stdout = io.StringIO()
        stderr = io.StringIO()
        with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
            result = governance.main(["--repo", str(self.repo), *arguments])
        return result, stdout.getvalue(), stderr.getvalue()

    def create_personal(self, filename="personal.md"):
        path = f"personal-prefernece/zhangsan/knowledge/guidelines/{filename}"
        result, _, error = self.run_command(
            "create",
            "--path",
            path,
            "--id",
            f"PK-{filename}",
            "--title",
            "个人排查经验",
            "--type",
            "guideline",
            "--layer",
            "layer0p",
            "--scope",
            "personal",
            "--owner-id",
            "zhangsan",
            "--source",
            "个人复盘",
            "--content",
            "调试 API 前先检查端口占用。",
            "--actor",
            "zhangsan",
            "--role",
            "contributor",
        )
        self.assertEqual(result, 0, error)
        return path

    def create_team(self, filename="team.md"):
        path = f"tech-wiki/patterns/{filename}"
        result, _, error = self.run_command(
            "create",
            "--path",
            path,
            "--id",
            f"TK-{filename}",
            "--title",
            "团队技术约定",
            "--type",
            "guideline",
            "--layer",
            "layer1",
            "--scope",
            "team",
            "--source",
            "架构评审",
            "--content",
            "治理脚本只使用 Python 标准库。",
            "--actor",
            "alice",
            "--role",
            "contributor",
        )
        self.assertEqual(result, 0, error)
        return path

    def create_team_convention(self, filename="convention.md"):
        path = f"team-conventions/guidelines/{filename}"
        result, _, error = self.run_command(
            "create",
            "--path",
            path,
            "--id",
            f"TC-{filename}",
            "--title",
            "团队协作约定",
            "--type",
            "guideline",
            "--layer",
            "layer0t",
            "--scope",
            "team",
            "--source",
            "团队评审",
            "--content",
            "提交前必须完成必要检查。",
            "--actor",
            "alice",
            "--role",
            "contributor",
        )
        self.assertEqual(result, 0, error)
        return path

    def reference(self, path, actor, project="project-a", workflow="flow-a", role="reader"):
        return self.run_command(
            "reference",
            path,
            "--project",
            project,
            "--workflow",
            workflow,
            "--used-in",
            "BUILD_VERIFY",
            "--actor",
            actor,
            "--role",
            role,
        )

    def validate(self, path, actor, project="project-a", workflow="flow-a"):
        return self.run_command(
            "validate",
            path,
            "--project",
            project,
            "--workflow",
            workflow,
            "--result",
            "passed",
            "--source",
            "复核工作流结果",
            "--actor",
            actor,
            "--role",
            "contributor",
        )

    def read_metadata(self, relative_path):
        return governance.read_entry(self.repo / relative_path)[0]

    def test_personal_knowledge_only_owner_can_reference_but_peer_can_validate(self):
        path = self.create_personal()

        denied, _, error = self.reference(path, "lisi")
        self.assertEqual(denied, 1)
        self.assertIn("仅允许所有者 zhangsan 消费", error)

        allowed, _, error = self.reference(path, "zhangsan")
        self.assertEqual(allowed, 0, error)
        validated, _, error = self.validate(path, "lisi")
        self.assertEqual(validated, 0, error)

        metadata = self.read_metadata(path)
        self.assertEqual(metadata["maturity"], "verified")
        self.assertEqual(metadata["evidence"]["references"][0]["contributor"], "zhangsan")
        self.assertEqual(metadata["evidence"]["validations"][0]["contributor"], "lisi")

    def test_validation_without_matching_reference_does_not_raise_maturity(self):
        path = self.create_team("validation-first.md")
        result, _, error = self.validate(path, "bob")
        self.assertEqual(result, 0, error)
        self.assertEqual(self.read_metadata(path)["maturity"], "draft")

    def test_two_projects_and_two_validators_can_be_approved_as_proven(self):
        path = self.create_team("proven.md")
        self.assertEqual(self.reference(path, "alice", "project-a", "flow-a")[0], 0)
        self.assertEqual(self.validate(path, "bob", "project-a", "flow-a")[0], 0)
        self.assertEqual(self.reference(path, "alice", "project-b", "flow-b")[0], 0)
        self.assertEqual(self.validate(path, "carol", "project-b", "flow-b")[0], 0)

        result, _, error = self.run_command(
            "approve-proven",
            path,
            "--actor",
            "maintainer-a",
            "--role",
            "maintainer",
        )
        self.assertEqual(result, 0, error)
        self.assertEqual(self.read_metadata(path)["maturity"], "proven")

    def test_personal_promotion_requires_owner_consent_and_becomes_team_knowledge(self):
        path = self.create_personal("promotion.md")
        self.assertEqual(self.reference(path, "zhangsan")[0], 0)
        self.assertEqual(self.validate(path, "lisi")[0], 0)

        denied, _, error = self.run_command(
            "propose-promotion",
            path,
            "--target-layer",
            "layer1",
            "--destination",
            "patterns",
            "--actor",
            "lisi",
            "--role",
            "contributor",
        )
        self.assertEqual(denied, 1)
        self.assertIn("所有者 zhangsan 明确确认", error)

        proposed, _, error = self.run_command(
            "propose-promotion",
            path,
            "--target-layer",
            "layer1",
            "--destination",
            "patterns",
            "--owner-approved-by",
            "zhangsan",
            "--actor",
            "lisi",
            "--role",
            "contributor",
        )
        self.assertEqual(proposed, 0, error)
        approved, _, error = self.run_command(
            "approve-promotion",
            path,
            "--actor",
            "maintainer-a",
            "--role",
            "maintainer",
        )
        self.assertEqual(approved, 0, error)

        target = "tech-wiki/patterns/promotion.md"
        metadata = self.read_metadata(target)
        self.assertEqual(metadata["scope"], "team")
        self.assertEqual(metadata["layer"], "layer1")
        self.assertNotIn("owner_id", metadata)
        self.assertEqual(metadata["promotion"]["previous_layers"][0]["from"], "layer0p")

    def test_personal_restore_requires_owner_confirmation_and_adds_no_reference(self):
        path = self.create_personal("restore.md")
        archived, _, error = self.run_command(
            "archive",
            path,
            "--reason",
            "测试归档",
            "--actor",
            "maintainer-a",
            "--role",
            "maintainer",
        )
        self.assertEqual(archived, 0, error)
        archive_path = "personal-prefernece/zhangsan/knowledge/archive/guidelines/restore.md"

        denied, _, error = self.run_command(
            "restore",
            archive_path,
            "--reason",
            "重新启用",
            "--actor",
            "maintainer-a",
            "--role",
            "maintainer",
        )
        self.assertEqual(denied, 1)
        self.assertIn("所有者 zhangsan 重新确认", error)

        restored, _, error = self.run_command(
            "restore",
            archive_path,
            "--reason",
            "重新启用",
            "--owner-confirmed-by",
            "zhangsan",
            "--actor",
            "maintainer-a",
            "--role",
            "maintainer",
        )
        self.assertEqual(restored, 0, error)
        self.assertEqual(self.read_metadata(path)["evidence"]["references"], [])

    def test_review_uses_effective_reference_and_returns_beijing_time(self):
        path = self.create_personal("review.md")
        metadata = self.read_metadata(path)
        metadata["created_at"] = "2026-01-01T00:00:00Z"
        metadata["evidence"]["references"] = [
            {
                "project_id": "project-a",
                "workflow_id": "flow-a",
                "contributor": "zhangsan",
                "referenced_at": "2026-01-05T00:00:00Z",
                "used_in": "IMPLEMENT",
            },
            {
                "project_id": "project-b",
                "workflow_id": "flow-b",
                "contributor": "lisi",
                "referenced_at": "2026-01-20T00:00:00Z",
                "used_in": "IMPLEMENT",
            },
        ]

        before_due = governance.knowledge_review(
            metadata,
            datetime(2026, 2, 3, 23, 59, 59, tzinfo=timezone.utc),
        )
        at_due = governance.knowledge_review(
            metadata,
            datetime(2026, 2, 4, tzinfo=timezone.utc),
        )

        self.assertEqual(before_due["next_review_at"], "2026-02-04T08:00:00+08:00")
        self.assertFalse(before_due["overdue"])
        self.assertTrue(at_due["overdue"])

        metadata["maturity"] = "proven"
        proven = governance.knowledge_review(
            metadata,
            datetime(2026, 3, 6, tzinfo=timezone.utc),
        )
        self.assertEqual(proven["next_review_at"], "2026-03-06T08:00:00+08:00")
        self.assertTrue(proven["overdue"])

    def test_draft_is_due_for_archive_after_thirty_days_without_reference(self):
        path = self.create_personal("stale.md")
        absolute_path = self.repo / path
        metadata, body = governance.read_entry(absolute_path)
        metadata["created_at"] = "2025-01-01T00:00:00Z"
        governance.write_entry(absolute_path, metadata, body)

        issues, actions = governance.lint_entries(
            self.repo,
            datetime(2025, 1, 31, tzinfo=timezone.utc),
        )
        self.assertTrue(any(item.startswith("ARCHIVE_DUE") for item in issues))
        self.assertIn((absolute_path, "archive"), actions)

    def test_verified_and_proven_decay_use_last_reference_time(self):
        verified_path = self.create_team("verified-decay.md")
        proven_path = self.create_team("proven-decay.md")

        verified_metadata, verified_body = governance.read_entry(self.repo / verified_path)
        verified_metadata["created_at"] = "2024-01-01T00:00:00Z"
        verified_metadata["maturity"] = "verified"
        verified_metadata["evidence"]["references"] = [
            {
                "project_id": "project-a",
                "workflow_id": "flow-a",
                "contributor": "alice",
                "referenced_at": "2025-01-01T00:00:00Z",
                "used_in": "IMPLEMENT",
            }
        ]
        governance.write_entry(self.repo / verified_path, verified_metadata, verified_body)

        proven_metadata, proven_body = governance.read_entry(self.repo / proven_path)
        proven_metadata["created_at"] = "2023-01-01T00:00:00Z"
        proven_metadata["maturity"] = "proven"
        proven_metadata["evidence"]["references"] = [
            {
                "project_id": "project-a",
                "workflow_id": "flow-a",
                "contributor": "alice",
                "referenced_at": "2024-01-01T00:00:00Z",
                "used_in": "IMPLEMENT",
            }
        ]
        governance.write_entry(self.repo / proven_path, proven_metadata, proven_body)

        _, verified_actions = governance.lint_entries(
            self.repo,
            datetime(2025, 1, 31, tzinfo=timezone.utc),
        )
        _, proven_actions = governance.lint_entries(
            self.repo,
            datetime(2024, 3, 1, tzinfo=timezone.utc),
        )
        self.assertIn((self.repo / verified_path, "draft"), verified_actions)
        self.assertIn((self.repo / proven_path, "verified"), proven_actions)

    def test_open_conflict_is_reported_and_blocks_maturity_upgrade(self):
        path = self.create_team("conflict.md")
        self.assertEqual(self.reference(path, "alice")[0], 0)
        result, _, error = self.run_command(
            "mark-conflict",
            path,
            "--reason",
            "与另一条约定矛盾",
            "--actor",
            "bob",
            "--role",
            "contributor",
        )
        self.assertEqual(result, 0, error)
        self.assertEqual(self.validate(path, "bob")[0], 0)
        self.assertEqual(self.read_metadata(path)["maturity"], "draft")

        issues, _ = governance.lint_entries(self.repo, datetime.now(timezone.utc))
        self.assertTrue(any(item.startswith("CONFLICT_OPEN") for item in issues))

    def test_workflow_counter_runs_lint_every_ten_and_thirty_day_check_reminds(self):
        governance.record_lint_run(
            self.repo,
            datetime(2026, 1, 1, tzinfo=timezone.utc),
        )
        for _ in range(9):
            result, _, error = self.run_command(
                "workflow-complete",
                "--at",
                "2026-01-02T00:00:00Z",
                "--actor",
                "knowledge-lint",
                "--role",
                "system",
            )
            self.assertEqual(result, 0, error)

        result, output, error = self.run_command(
            "workflow-complete",
            "--at",
            "2026-01-02T00:00:00Z",
            "--actor",
            "knowledge-lint",
            "--role",
            "system",
        )
        self.assertEqual(result, 0, error)
        self.assertIn("自动执行 Lint", output)
        self.assertEqual(governance.read_governance_state(self.repo)["workflows_since_lint"], 0)

        result, output, error = self.run_command(
            "workflow-start",
            "--at",
            "2026-02-02T00:00:00Z",
            "--actor",
            "alice",
            "--role",
            "reader",
        )
        self.assertEqual(result, 0, error)
        self.assertIn("31 天", output)

    def test_catalogs_include_personal_and_team_scope(self):
        self.create_personal("catalog-entry.md")
        self.create_team_convention("catalog-entry.md")
        self.create_team("catalog-entry.md")
        root_catalog = (self.repo / "knowledge-catalog.md").read_text(encoding="utf-8")
        personal_catalog = (
            self.repo / "personal-prefernece/zhangsan/knowledge/catalog.md"
        ).read_text(encoding="utf-8")
        team_catalog = (self.repo / "tech-wiki/catalog.md").read_text(encoding="utf-8")
        convention_catalog = (self.repo / "team-conventions/catalog.md").read_text(
            encoding="utf-8"
        )

        self.assertIn("Layer 0-P | 1", root_catalog)
        self.assertIn("Layer 0-T | 1", root_catalog)
        self.assertIn("`personal`", personal_catalog)
        self.assertIn("`team`", convention_catalog)
        self.assertIn("`team`", team_catalog)

    def test_layer0t_keeps_legacy_root_documents_outside_structured_governance(self):
        root = self.repo / "team-conventions"
        root.mkdir(parents=True)
        legacy = root / "commit-conventions.md"
        legacy.write_text("# 既有团队约定\n", encoding="utf-8")

        self.create_team_convention()
        issues, _actions = governance.lint_entries(
            self.repo,
            datetime(2026, 1, 1, tzinfo=timezone.utc),
        )

        self.assertFalse(any("commit-conventions.md" in issue for issue in issues))
        self.assertEqual(legacy.read_text(encoding="utf-8"), "# 既有团队约定\n")

    def test_layer1_accepts_type_directories_and_legacy_direction_directories(self):
        result, _, error = self.run_command(
            "create",
            "--path",
            "tech-wiki/guidelines/invalid.md",
            "--id",
            "TK-GDL-999",
            "--title",
            "错误目录示例",
            "--type",
            "guideline",
            "--layer",
            "layer1",
            "--scope",
            "team",
            "--source",
            "测试",
            "--content",
            "Layer 1 新知识按五种知识类型建立目录。",
            "--actor",
            "alice",
            "--role",
            "contributor",
        )
        self.assertEqual(result, 0, error)

        result, _, error = self.run_command(
            "create",
            "--path",
            "tech-wiki/unknown/invalid.md",
            "--id",
            "TK-GDL-998",
            "--title",
            "错误目录示例",
            "--type",
            "guideline",
            "--layer",
            "layer1",
            "--scope",
            "team",
            "--source",
            "测试",
            "--content",
            "Layer 1 不能写入未知目录。",
            "--actor",
            "alice",
            "--role",
            "contributor",
        )
        self.assertEqual(result, 1)
        self.assertIn("guidelines/", error)

    def test_admin_revision_preserves_old_evidence_but_only_current_revision_counts(self):
        relative = self.create_team("revisioned.md")
        referenced, _, error = self.reference(relative, "alice")
        self.assertEqual(referenced, 0, error)
        validated, _, error = self.validate(relative, "bob")
        self.assertEqual(validated, 0, error)
        path = self.repo / relative
        metadata, body = governance.read_entry(path)
        self.assertEqual(metadata["revision"], 1)
        self.assertEqual(metadata["maturity"], "verified")
        self.assertEqual(metadata["evidence"]["references"][0]["revision"], 1)
        self.assertEqual(metadata["evidence"]["validations"][0]["revision"], 1)

        updated, written_path, action = governance.update_knowledge_entry(
            repo=self.repo,
            source_path=path,
            target_path=path,
            updates={
                "title": "团队技术约定（修订）",
                "type": metadata["type"],
                "layer": metadata["layer"],
                "scope": governance.metadata_scope(metadata),
                "tags": metadata["tags"],
                "source_references": metadata["source_references"],
                "technical_direction": metadata.get("technical_direction"),
                "owner_id": metadata.get("owner_id"),
            },
            content="治理脚本仍只使用 Python 标准库。",
            actor="root",
            role="super_admin",
            reason="修订知识正文",
            request_id="revision-test-request",
        )
        self.assertEqual(action, "admin-knowledge-update")
        self.assertEqual(written_path, path.resolve())
        self.assertEqual(updated["revision"], 2)
        self.assertEqual(updated["maturity"], "draft")
        self.assertFalse(governance.eligible_for_verified(updated))
        self.assertEqual(len(updated["evidence"]["references"]), 1)
        self.assertEqual(len(updated["evidence"]["validations"]), 1)

        referenced, _, error = self.reference(relative, "alice", role="super_admin")
        self.assertEqual(referenced, 0, error)
        validated, _, error = self.run_command(
            "validate",
            relative,
            "--project",
            "project-a",
            "--workflow",
            "flow-a",
            "--result",
            "passed",
            "--source",
            "修订后复核",
            "--actor",
            "bob",
            "--role",
            "super_admin",
        )
        self.assertEqual(validated, 0, error)
        current = self.read_metadata(relative)
        self.assertEqual(current["maturity"], "verified")
        self.assertEqual(current["evidence"]["references"][-1]["revision"], 2)
        self.assertEqual(current["evidence"]["validations"][-1]["revision"], 2)


if __name__ == "__main__":
    unittest.main()
