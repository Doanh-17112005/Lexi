import { apiFetch } from "./api";
import { ENV } from "./env";

export type GenerateLessonRequest = {
  topic: string;
  cefr_level: "A1" | "A2" | "B1" | "B2" | "C1" | "C2";
  source_text: string;
};

export type GeneratedLesson = {
  success: boolean;
  message: string;
  course: { id: string; title: string; level: string };
  unit: { id: string; title: string; order_index: number };
  lesson: {
    id: string;
    title: string;
    description: string;
    outcome: string;
    estimated_minutes: number;
    total_exercises: number;
    xp_reward: number;
  };
  vocabulary_saved: number;
  vocabulary: Array<{
    word: string;
    pronunciation?: string | null;
    definition: string;
    translation_vi: string;
    example: string;
    part_of_speech: string;
  }>;
  quizzes: Array<{
    question: string;
    options: string[];
    correct_answer: string;
    explanation: string;
  }>;
};

export const generateAiLesson = (request: GenerateLessonRequest) =>
  apiFetch<GeneratedLesson>(
    `${ENV.backendUrl}/admin/ai-content/generate-lesson`,
    {
      method: "POST",
      body: JSON.stringify(request),
    },
  );
