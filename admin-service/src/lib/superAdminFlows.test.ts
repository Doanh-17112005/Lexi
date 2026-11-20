import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { ApiError } from "./api";
import { authStore, resolveRole } from "./auth";
import { getAdminLoginErrorMessage } from "./adminLoginError";
import { getDashboardKPIs, getUserGrowth } from "./analyticsApi";
import { getDashboardStats } from "./rbacApi";
import {
  bulkUserAction,
  getUsers,
  permanentlyDeleteUser,
  updateUserRole,
  updateUserStatus,
} from "./userManagementApi";
import {
  createGrammar,
  createLesson,
  createQuestion,
  createTestExam,
  createUnit,
  listVocabulary,
  updateCourse,
  updateLessonContent,
  updateVocabulary,
} from "./adminApi";
import {
  applyContentAgentJob,
  getContentAgentPreview,
  listContentQaQueue,
  updateContentAgentRecord,
} from "./contentAgentApi";
import { canToggleAdminStatus } from "../pages/AdminManagementPage";
import { defaultExercise } from "../pages/LessonExercisesPage";

const jsonResponse = (body: unknown, status = 200) =>
  new Response(JSON.stringify(body), {
    status,
    headers: { "Content-Type": "application/json" },
  });

const makeJwt = (secondsFromNow = 3600) => {
  const payload = btoa(
    JSON.stringify({ exp: Math.floor(Date.now() / 1000) + secondsFromNow }),
  );
  return `header.${payload}.signature`;
};

const makeStorage = () => {
  const store = new Map<string, string>();
  return {
    getItem: (key: string) => store.get(key) ?? null,
    setItem: (key: string, value: string) => {
      store.set(key, value);
    },
    removeItem: (key: string) => {
      store.delete(key);
    },
    clear: () => {
      store.clear();
    },
  };
};

describe("Super Admin QA fixture flows (isolated, zero live DB)", () => {
  beforeEach(() => {
    vi.stubGlobal("localStorage", makeStorage());
    vi.stubGlobal("window", {
      atob: (value: string) => atob(value),
      location: { href: "" },
    });
    authStore.accessToken = makeJwt(3600);
    authStore.refreshToken = "test-refresh-token";
  });

  afterEach(() => {
    vi.unstubAllGlobals();
    vi.restoreAllMocks();
  });

  it("1. Auth/RBAC rejects non-admin roles and surfaces 403 error cleanly", async () => {
    expect(
      resolveRole({
        id: "u-learner",
        email: "learner@example.com",
        username: "learner",
        role: "user",
        is_admin: false,
        is_super_admin: false,
      }),
    ).toBeNull();

    expect(
      resolveRole({
        id: "u-super",
        email: "super@example.com",
        username: "super",
        role_slug: "super_admin",
      }),
    ).toBe("super_admin");

    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(
        jsonResponse({ detail: "Admin access required" }, 403),
      ),
    );

    await expect(getDashboardKPIs()).rejects.toMatchObject({
      status: 403,
      message: "Admin access required",
    });
    expect(getAdminLoginErrorMessage(new ApiError("Forbidden", 403))).toContain(
      "không có quyền",
    );
  });

  it("2. Dashboard KPIs and RBAC stats parse expected backend envelopes", async () => {
    const fetchMock = vi
      .fn()
      .mockResolvedValueOnce(
        jsonResponse({
          kpis: {
            total_users: 29,
            active_users_7d: 14,
            total_courses: 6,
            total_lessons_completed_today: 8,
            avg_dau_30d: 6.5,
          },
        }),
      )
      .mockResolvedValueOnce(
        jsonResponse({
          dashboard: {
            total_users: 29,
            active_users: 25,
            users_by_role: { user: 27, admin: 1, super_admin: 1 },
            total_achievements: 48,
            total_unlocks: 12,
            recent_actions: [],
          },
        }),
      )
      .mockResolvedValueOnce(
        jsonResponse({
          data: [{ date: "2026-11-18", new_users: 2, total_users: 29 }],
        }),
      );
    vi.stubGlobal("fetch", fetchMock);

    const kpis = await getDashboardKPIs();
    const stats = await getDashboardStats();
    const growth = await getUserGrowth(30);

    expect(kpis.kpis.total_users).toBe(29);
    expect(stats.dashboard.total_achievements).toBe(48);
    expect(growth.data).toHaveLength(1);
  });

  it("3. User Management supports pagination/filter, status toggle, bulk action, and permanent delete", async () => {
    const fetchMock = vi
      .fn()
      .mockResolvedValueOnce(
        jsonResponse({
          success: true,
          data: {
            users: [
              {
                id: "u-1",
                email: "alice@example.com",
                username: "alice",
                display_name: "Alice",
                is_active: true,
                is_verified: true,
                role_slug: "user",
                role_level: 0,
                created_at: "2026-11-01T00:00:00Z",
                last_login: null,
              },
            ],
            total: 1,
            page: 2,
            page_size: 20,
            total_pages: 2,
          },
        }),
      )
      .mockResolvedValueOnce(
        jsonResponse({
          success: true,
          data: { message: "Updated", user_id: "u-1", is_active: false },
        }),
      )
      .mockResolvedValueOnce(
        jsonResponse({
          success: true,
          data: { message: "Bulk done", updated_count: 1, requested_count: 1 },
        }),
      )
      .mockResolvedValueOnce(
        jsonResponse({
          success: true,
          data: { message: "Deleted", user_id: "u-1" },
        }),
      );
    vi.stubGlobal("fetch", fetchMock);

    const list = await getUsers({
      page: 2,
      page_size: 20,
      search: "alice",
      role: 0,
      is_active: true,
    });
    expect(list.users).toHaveLength(1);
    const listUrl = String(fetchMock.mock.calls[0][0]);
    expect(listUrl).toContain("page=2");
    expect(listUrl).toContain("search=alice");
    expect(listUrl).toContain("role=0");
    expect(listUrl).toContain("is_active=true");

    const statusRes = await updateUserStatus("u-1", { is_active: false });
    expect(statusRes.is_active).toBe(false);

    const bulkRes = await bulkUserAction({
      user_ids: ["u-1"],
      action: "deactivate",
    });
    expect(bulkRes.updated_count).toBe(1);

    const delRes = await permanentlyDeleteUser("u-1");
    expect(delRes.user_id).toBe("u-1");
    expect(fetchMock.mock.calls[3][1].method).toBe("DELETE");
  });

  it("4. Courses/Units/Lessons/Exercises publish & edit contracts align with backend", async () => {
    const fetchMock = vi
      .fn()
      .mockResolvedValueOnce(
        jsonResponse(
          { detail: "Cannot publish this course: Lesson 1 has no exercises" },
          409,
        ),
      )
      .mockResolvedValueOnce(
        jsonResponse({ success: true, data: { id: "unit-1", order_index: 0 } }),
      )
      .mockResolvedValueOnce(
        jsonResponse({ success: true, data: { id: "lesson-1", order_index: 0 } }),
      )
      .mockResolvedValueOnce(
        jsonResponse({
          success: true,
          data: { id: "lesson-1", exercise_count: 1, estimated_minutes: 12 },
        }),
      );
    vi.stubGlobal("fetch", fetchMock);

    await expect(
      updateCourse("course-1", { is_published: true }),
    ).rejects.toMatchObject({
      status: 409,
    });

    await createUnit({
      course_id: "course-1",
      title: "Unit 0",
      order_index: 0,
    });
    expect(JSON.parse(fetchMock.mock.calls[1][1].body).order_index).toBe(0);

    await createLesson({
      unit_id: "unit-1",
      title: "Lesson 0",
      order_index: 0,
      lesson_type: "lesson",
    });
    expect(JSON.parse(fetchMock.mock.calls[2][1].body).order_index).toBe(0);

    const tfExercise = defaultExercise("true_or_false", 0);
    tfExercise.question = "Water boils at 50°C.";
    await updateLessonContent("lesson-1", [tfExercise], 12);
    const contentBody = JSON.parse(fetchMock.mock.calls[3][1].body);
    expect(contentBody.total_exercises).toBeUndefined();
    expect(contentBody.estimated_minutes).toBe(12);
    expect(contentBody.content.exercises[0].correct_answer).toBe("False");
  });

  it("5. Vocabulary CEFR/topic/QA filter and non-destructive update preserve contract", async () => {
    const fetchMock = vi
      .fn()
      .mockResolvedValueOnce(
        jsonResponse({
          success: true,
          data: [
            {
              id: "v-1",
              word: "resilient",
              part_of_speech: "adjective",
              difficulty_level: "B2",
              topics: ["business"],
              qa_status: "NEEDS_REVIEW",
            },
          ],
        }),
      )
      .mockResolvedValueOnce(
        jsonResponse({
          success: true,
          data: {
            id: "v-1",
            word: "resilient",
            part_of_speech: "adjective",
            difficulty_level: "B2",
            topics: ["business"],
            qa_status: "VERIFIED",
            source_reference: "Cambridge Dictionary",
          },
        }),
      );
    vi.stubGlobal("fetch", fetchMock);

    const list = await listVocabulary(100, 0, {
      search: "resil",
      difficulty_level: "B2",
      topic: "business",
      qa_status: "NEEDS_REVIEW",
    });
    expect(list.data).toHaveLength(1);
    const url = String(fetchMock.mock.calls[0][0]);
    expect(url).toContain("difficulty_level=B2");
    expect(url).toContain("topic=business");
    expect(url).toContain("qa_status=NEEDS_REVIEW");

    const updated = await updateVocabulary("v-1", {
      translation: "kiên cường",
      topics: "business",
      qa_status: "VERIFIED",
      source_reference: "Cambridge Dictionary",
    });
    expect(updated.data?.qa_status).toBe("VERIFIED");
    const putUrl = String(fetchMock.mock.calls[1][0]);
    expect(putUrl).toContain("qa_status=VERIFIED");
    expect(putUrl).toContain("source_reference=Cambridge+Dictionary");
    expect(putUrl).not.toContain("word=");
  });

  it("6. ContentLab CRUD & Content QA queue preview/edit/apply payloads match backend", async () => {
    const sampleJob = {
      id: "job-1",
      status: "preview_ready",
      config: {},
      progress: {},
      source_manifest: [],
      warnings: [],
      blocking_errors: [],
      created_entity_ids: {},
      created_at: "",
      updated_at: "",
    };
    const fetchMock = vi
      .fn()
      .mockResolvedValueOnce(jsonResponse({ success: true, data: { id: "g-1" } }))
      .mockResolvedValueOnce(jsonResponse({ success: true, data: { id: "q-1" } }))
      .mockResolvedValueOnce(jsonResponse({ success: true, data: { id: "t-1" } }))
      .mockResolvedValueOnce(
        jsonResponse({
          success: true,
          data: { jobs: [sampleJob], total: 1 },
        }),
      )
      .mockResolvedValueOnce(
        jsonResponse({
          success: true,
          data: {
            schema_version: 1,
            prompt_version: "v1",
            generation_key: "gk",
            source_manifest: [],
            courses: [],
            quality: { blocking_errors: [], warnings: [], metrics: {} },
          },
        }),
      )
      .mockResolvedValueOnce(
        jsonResponse({
          success: true,
          data: {
            schema_version: 1,
            prompt_version: "v1",
            generation_key: "gk",
            source_manifest: [],
            courses: [],
            quality: { blocking_errors: [], warnings: [], metrics: {} },
          },
        }),
      )
      .mockResolvedValueOnce(
        jsonResponse({
          success: true,
          data: { ...sampleJob, status: "completed" },
        }),
      );
    vi.stubGlobal("fetch", fetchMock);

    await createGrammar({
      title: "Present Simple",
      level: "A1",
      content: "S + V(s/es)",
    });
    await createQuestion({
      prompt: "She ___ to school.",
      question_type: "mcq",
      difficulty_level: "A1",
      options: ["go", "goes"],
      answer: "goes",
    });
    await createTestExam({
      title: "A1 Check",
      level: "A1",
      duration_minutes: 15,
      passing_score: 70,
    });

    const queue = await listContentQaQueue();
    expect(queue.reviewable).toHaveLength(1);
    await getContentAgentPreview("job-1");
    await updateContentAgentRecord("job-1", "rec-1", {
      question: "Updated question",
      correct_answer: "goes",
    });
    const applied = await applyContentAgentJob("job-1");
    expect(applied.status).toBe("completed");
  });

  it("7. AdminManagement enforces self-deactivation guard and role promotion payload", async () => {
    expect(canToggleAdminStatus("admin-1", "admin-1")).toBe(false);
    expect(canToggleAdminStatus("", "admin-1")).toBe(false);
    expect(canToggleAdminStatus("admin-2", "admin-1")).toBe(true);

    const fetchMock = vi.fn().mockResolvedValueOnce(
      jsonResponse({
        success: true,
        data: { message: "Role updated", user_id: "admin-2", new_level: 1 },
      }),
    );
    vi.stubGlobal("fetch", fetchMock);

    const roleRes = await updateUserRole("admin-2", { level: 1 });
    expect(roleRes.new_level).toBe(1);
    expect(JSON.parse(fetchMock.mock.calls[0][1].body)).toEqual({ level: 1 });
  });
});
