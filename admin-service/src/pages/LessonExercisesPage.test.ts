import { describe, expect, it } from "vitest";
import { UI_TYPES, UI_TYPE_TO_TYPE } from "../lib/adminApi";
import { defaultExercise } from "./LessonExercisesPage";

describe("LessonExercisesPage defaultExercise", () => {
  it("initializes true_or_false with False selected and matching options", () => {
    const ex = defaultExercise("true_or_false", 0);
    expect(ex.ui_type).toBe("true_or_false");
    expect(ex.type).toBe(UI_TYPE_TO_TYPE.true_or_false);
    expect(ex.correct_answer).toBe("False");
    expect(ex.options).toEqual([
      { id: "0", text: "True", is_correct: false },
      { id: "1", text: "False", is_correct: true },
    ]);
  });

  it("maps every supported ui_type to its backend exercise type", () => {
    for (const uiType of UI_TYPES) {
      const ex = defaultExercise(uiType, 0);
      expect(ex.type).toBe(UI_TYPE_TO_TYPE[uiType]);
      expect(ex.points).toBeGreaterThan(0);
    }
  });
});
