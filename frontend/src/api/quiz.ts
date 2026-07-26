import api from "./client";

export async function generateQuiz(
  topicId: number,
  numQuestions: number = 5,
  quizType: string = "practice"
) {
  const res = await api.post(`/quiz/generate/${topicId}`, {
    num_questions: numQuestions,
    quiz_type: quizType,
  });
  return res.data;
}

export async function getQuiz(quizId: number) {
  const res = await api.get(`/quiz/${quizId}`);
  return res.data;
}

export async function submitQuiz(
  quizId: number,
  answers: { question_id: number; selected_option_id: number }[]
) {
  const res = await api.post(`/quiz/${quizId}/submit`, { answers });
  return res.data;
}
