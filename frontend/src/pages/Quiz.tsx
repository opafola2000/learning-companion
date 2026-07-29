import { useState, useEffect } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { generateQuiz, submitQuiz } from "../api/quiz";
import LoadingSpinner from "../components/LoadingSpinner";
import TrustDisclaimer from "../components/TrustDisclaimer";
import ReportContentButton from "../components/ReportContentButton";

interface AnswerOption {
  id: number;
  option_text: string;
  is_correct?: boolean;
}

interface Question {
  id: number;
  question_text: string;
  difficulty: string;
  explanation?: string | null;
  objective_id?: string | null;
  source_reference?: string | null;
  citation_snippet?: string | null;
  options: AnswerOption[];
  user_selected_option_id?: number | null;
  is_correct?: boolean | null;
}

interface QuizData {
  id: number;
  topic_id: number;
  quiz_type: string;
  num_questions: number;
  exam_code?: string | null;
  blueprint_version?: string | null;
  validation_status?: string | null;
  questions: Question[];
}

interface QuizResult {
  attempt_id: number;
  score: number;
  total_questions: number;
  correct_count: number;
  questions: Question[];
  mastery_update: number | null;
  exam_code?: string | null;
  blueprint_version?: string | null;
}

type Phase = "generating" | "taking" | "submitted";

export default function Quiz() {
  const { topicId } = useParams<{ topicId: string }>();
  const navigate = useNavigate();
  const [phase, setPhase] = useState<Phase>("generating");
  const [quiz, setQuiz] = useState<QuizData | null>(null);
  const [selectedAnswers, setSelectedAnswers] = useState<
    Record<number, number>
  >({});
  const [result, setResult] = useState<QuizResult | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    if (topicId) {
      generateQuiz(parseInt(topicId))
        .then((data) => {
          setQuiz(data);
          setPhase("taking");
        })
        .catch((err) => {
          setError(
            err.response?.data?.detail || "Failed to generate quiz"
          );
        });
    }
  }, [topicId]);

  function handleSelect(questionId: number, optionId: number) {
    if (phase !== "taking") return;
    setSelectedAnswers((prev) => ({ ...prev, [questionId]: optionId }));
  }

  async function handleSubmit() {
    if (!quiz) return;
    setSubmitting(true);
    setError("");
    try {
      const answers = Object.entries(selectedAnswers).map(([qId, oId]) => ({
        question_id: parseInt(qId),
        selected_option_id: oId,
      }));
      const res = await submitQuiz(quiz.id, answers);
      setResult(res);
      setPhase("submitted");
    } catch (err: any) {
      setError(err.response?.data?.detail || "Submission failed");
    } finally {
      setSubmitting(false);
    }
  }

  if (error && phase === "generating") {
    return (
      <div className="max-w-3xl mx-auto px-4 py-12 text-center">
        <div className="bg-red-50 border border-red-200 text-red-700 rounded-lg p-4">
          {error}
        </div>
        <button
          onClick={() => navigate(-1)}
          className="mt-4 text-indigo-600 hover:underline"
        >
          Go back
        </button>
      </div>
    );
  }

  if (phase === "generating") {
    return <LoadingSpinner message="Generating quiz questions..." />;
  }

  const questions = phase === "submitted" && result ? result.questions : quiz?.questions || [];
  const allAnswered = quiz
    ? quiz.questions.every((q) => selectedAnswers[q.id] !== undefined)
    : false;

  return (
    <div className="max-w-3xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <button
        onClick={() => navigate(-1)}
        className="text-sm text-indigo-600 hover:underline mb-4 inline-block"
      >
        &larr; Back
      </button>

      <div className="mb-4">
        <TrustDisclaimer />
      </div>

      {quiz && (quiz.exam_code || quiz.blueprint_version) && (
        <div className="flex flex-wrap gap-2 mb-4">
          {quiz.exam_code && (
            <span className="text-xs px-2 py-1 rounded-full bg-indigo-50 text-indigo-700">
              Exam: {quiz.exam_code}
            </span>
          )}
          {quiz.blueprint_version && (
            <span className="text-xs px-2 py-1 rounded-full bg-blue-50 text-blue-700">
              Blueprint: {quiz.blueprint_version}
            </span>
          )}
          {quiz.validation_status && (
            <span className="text-xs px-2 py-1 rounded-full bg-green-50 text-green-700">
              {quiz.validation_status.replace("_", " ")}
            </span>
          )}
        </div>
      )}

      {/* Score banner */}
      {phase === "submitted" && result && (
        <div
          className={`rounded-xl p-6 mb-6 ${
            result.score >= 80
              ? "bg-green-50 border border-green-200"
              : result.score >= 60
              ? "bg-blue-50 border border-blue-200"
              : "bg-yellow-50 border border-yellow-200"
          }`}
        >
          <div className="flex justify-between items-center">
            <div>
              <h2 className="text-2xl font-bold">
                Score: {Math.round(result.score)}%
              </h2>
              <p className="text-sm mt-1">
                {result.correct_count} of {result.total_questions} correct
              </p>
            </div>
            {result.mastery_update !== null && (
              <div className="text-right">
                <div className="text-sm text-gray-500">Topic Mastery</div>
                <div className="text-xl font-bold text-indigo-600">
                  {Math.round(result.mastery_update)}%
                </div>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Questions */}
      <div className="space-y-6">
        {questions.map((q, idx) => {
          const isSubmitted = phase === "submitted";
          const userSelected = isSubmitted
            ? q.user_selected_option_id
            : selectedAnswers[q.id];

          return (
            <div
              key={q.id}
              className="bg-white rounded-xl border border-gray-200 p-6"
            >
              <div className="flex items-start gap-3 mb-4">
                <span className="flex-shrink-0 w-7 h-7 rounded-full bg-indigo-100 text-indigo-700 flex items-center justify-center text-sm font-bold">
                  {idx + 1}
                </span>
                <div>
                  <p className="font-medium text-gray-900 whitespace-pre-wrap">
                    {q.question_text}
                  </p>
                  <span
                    className={`text-xs mt-1 inline-block px-2 py-0.5 rounded-full ${
                      q.difficulty === "advanced"
                        ? "bg-red-50 text-red-600"
                        : q.difficulty === "intermediate"
                        ? "bg-yellow-50 text-yellow-600"
                        : "bg-green-50 text-green-600"
                    }`}
                  >
                    {q.difficulty}
                  </span>
                </div>
              </div>

              <div className="space-y-2 ml-10">
                {q.options.map((opt) => {
                  let optionClasses =
                    "w-full text-left p-3 rounded-lg border text-sm transition-colors ";

                  if (isSubmitted) {
                    if (opt.is_correct) {
                      optionClasses +=
                        "border-green-400 bg-green-50 text-green-800";
                    } else if (opt.id === userSelected && !opt.is_correct) {
                      optionClasses +=
                        "border-red-400 bg-red-50 text-red-800";
                    } else {
                      optionClasses +=
                        "border-gray-200 bg-gray-50 text-gray-500";
                    }
                  } else {
                    if (opt.id === userSelected) {
                      optionClasses +=
                        "border-indigo-500 bg-indigo-50 text-indigo-800";
                    } else {
                      optionClasses +=
                        "border-gray-200 hover:border-indigo-300 hover:bg-indigo-50 text-gray-700";
                    }
                  }

                  return (
                    <button
                      key={opt.id}
                      onClick={() => handleSelect(q.id, opt.id)}
                      disabled={isSubmitted}
                      className={optionClasses}
                    >
                      {opt.option_text}
                    </button>
                  );
                })}
              </div>

              {/* Explanation */}
              {isSubmitted && q.explanation && (
                <div className="mt-4 ml-10 p-3 bg-blue-50 border border-blue-200 rounded-lg text-sm text-blue-800">
                  <strong>Explanation:</strong> {q.explanation}
                  {q.objective_id && (
                    <p className="text-xs mt-2 text-blue-600">
                      Objective: {q.objective_id}
                    </p>
                  )}
                  {q.source_reference && (
                    <p className="text-xs mt-1 text-blue-600">
                      Source: {q.source_reference}
                    </p>
                  )}
                  {q.citation_snippet && (
                    <p className="text-xs mt-1 italic text-blue-700">
                      &ldquo;{q.citation_snippet}&rdquo;
                    </p>
                  )}
                  <div className="mt-2">
                    <ReportContentButton contentType="question" contentId={q.id} />
                  </div>
                </div>
              )}
            </div>
          );
        })}
      </div>

      {/* Submit / Retry */}
      <div className="mt-8 flex justify-center gap-4">
        {phase === "taking" && (
          <button
            onClick={handleSubmit}
            disabled={!allAnswered || submitting}
            className="px-8 py-3 bg-indigo-600 text-white rounded-lg font-medium hover:bg-indigo-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            {submitting
              ? "Submitting..."
              : `Submit Answers (${Object.keys(selectedAnswers).length}/${quiz?.questions.length || 0})`}
          </button>
        )}
        {phase === "submitted" && (
          <>
            <button
              onClick={() => {
                setPhase("generating");
                setSelectedAnswers({});
                setResult(null);
                generateQuiz(parseInt(topicId!))
                  .then((data) => {
                    setQuiz(data);
                    setPhase("taking");
                  })
                  .catch((err) =>
                    setError(err.response?.data?.detail || "Failed to generate quiz")
                  );
              }}
              className="px-6 py-3 bg-indigo-600 text-white rounded-lg font-medium hover:bg-indigo-700 transition-colors"
            >
              Try Another Quiz
            </button>
            <button
              onClick={() => navigate(-1)}
              className="px-6 py-3 border border-gray-300 text-gray-700 rounded-lg font-medium hover:bg-gray-50 transition-colors"
            >
              Back to Curriculum
            </button>
          </>
        )}
      </div>

      {error && (
        <div className="mt-4 bg-red-50 border border-red-200 text-red-700 rounded-lg p-3 text-sm text-center">
          {error}
        </div>
      )}
    </div>
  );
}
