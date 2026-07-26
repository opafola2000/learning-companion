import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { listCurricula } from "../api/curriculum";
import { getCurriculumProgress, getRecommendations } from "../api/progress";
import LoadingSpinner from "../components/LoadingSpinner";
import MasteryBadge from "../components/MasteryBadge";

interface TopicProgress {
  topic_id: number;
  topic_title: string;
  module_title: string;
  mastery_score: number;
  attempts_count: number;
  last_assessed: string | null;
  status: string;
}

interface CurriculumProgress {
  curriculum_id: number;
  skill_name: string;
  overall_mastery: number;
  topics: TopicProgress[];
}

interface Recommendation {
  topic_id: number;
  topic_title: string;
  module_title: string;
  current_mastery: number;
  recommendation_type: string;
  reason: string;
}

export default function Progress() {
  const navigate = useNavigate();
  const [progressData, setProgressData] = useState<CurriculumProgress[]>([]);
  const [recommendations, setRecommendations] = useState<Recommendation[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedCurriculum, setSelectedCurriculum] = useState<number | null>(null);

  useEffect(() => {
    loadAllProgress();
  }, []);

  async function loadAllProgress() {
    try {
      const [curricula, recs] = await Promise.all([
        listCurricula(),
        getRecommendations(),
      ]);
      setRecommendations(recs);

      const progressResults = await Promise.all(
        curricula.map((c: any) => getCurriculumProgress(c.id).catch(() => null))
      );
      const valid = progressResults.filter(Boolean) as CurriculumProgress[];
      setProgressData(valid);
      if (valid.length > 0) {
        setSelectedCurriculum(valid[0].curriculum_id);
      }
    } catch {
      // ignore
    } finally {
      setLoading(false);
    }
  }

  if (loading) return <LoadingSpinner />;

  const currentProgress = progressData.find(
    (p) => p.curriculum_id === selectedCurriculum
  );

  const groupedByModule: Record<string, TopicProgress[]> = {};
  if (currentProgress) {
    for (const t of currentProgress.topics) {
      if (!groupedByModule[t.module_title]) {
        groupedByModule[t.module_title] = [];
      }
      groupedByModule[t.module_title].push(t);
    }
  }

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <h1 className="text-2xl font-bold text-gray-900 mb-6">
        Learning Progress
      </h1>

      {progressData.length === 0 ? (
        <div className="bg-white rounded-xl border border-gray-200 p-12 text-center">
          <p className="text-gray-400 text-lg">No progress data yet.</p>
          <p className="text-gray-400 mt-2">
            Generate a curriculum and take quizzes to track your progress.
          </p>
          <button
            onClick={() => navigate("/")}
            className="mt-4 px-6 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 transition-colors"
          >
            Go to Dashboard
          </button>
        </div>
      ) : (
        <div className="grid grid-cols-1 lg:grid-cols-4 gap-8">
          {/* Main progress */}
          <div className="lg:col-span-3">
            {/* Curriculum selector */}
            {progressData.length > 1 && (
              <div className="mb-6">
                <select
                  value={selectedCurriculum ?? ""}
                  onChange={(e) =>
                    setSelectedCurriculum(parseInt(e.target.value))
                  }
                  className="px-4 py-2 border border-gray-300 rounded-lg"
                >
                  {progressData.map((p) => (
                    <option key={p.curriculum_id} value={p.curriculum_id}>
                      {p.skill_name} ({Math.round(p.overall_mastery)}%)
                    </option>
                  ))}
                </select>
              </div>
            )}

            {/* Overall mastery */}
            {currentProgress && (
              <div className="bg-white rounded-xl border border-gray-200 p-6 mb-6">
                <div className="flex justify-between items-center mb-3">
                  <h2 className="text-lg font-semibold text-gray-900">
                    {currentProgress.skill_name}
                  </h2>
                  <span className="text-3xl font-bold text-indigo-600">
                    {Math.round(currentProgress.overall_mastery)}%
                  </span>
                </div>
                <div className="w-full bg-gray-100 rounded-full h-3">
                  <div
                    className="bg-indigo-600 h-3 rounded-full transition-all"
                    style={{
                      width: `${Math.min(currentProgress.overall_mastery, 100)}%`,
                    }}
                  ></div>
                </div>
              </div>
            )}

            {/* Per-module breakdown */}
            {Object.entries(groupedByModule).map(([moduleName, topics]) => {
              const avgMastery =
                topics.reduce((sum, t) => sum + t.mastery_score, 0) /
                topics.length;

              return (
                <div
                  key={moduleName}
                  className="bg-white rounded-xl border border-gray-200 p-6 mb-4"
                >
                  <div className="flex justify-between items-center mb-4">
                    <h3 className="font-semibold text-gray-900">
                      {moduleName}
                    </h3>
                    <span className="text-sm font-medium text-gray-500">
                      {Math.round(avgMastery)}% avg
                    </span>
                  </div>
                  <div className="space-y-3">
                    {topics.map((topic) => (
                      <div
                        key={topic.topic_id}
                        className="flex items-center justify-between"
                      >
                        <div className="flex-1 mr-4">
                          <p className="text-sm font-medium text-gray-800">
                            {topic.topic_title}
                          </p>
                          <div className="mt-1 w-full bg-gray-100 rounded-full h-2">
                            <div
                              className={`h-2 rounded-full transition-all ${
                                topic.mastery_score >= 80
                                  ? "bg-green-500"
                                  : topic.mastery_score >= 60
                                  ? "bg-blue-500"
                                  : topic.mastery_score >= 30
                                  ? "bg-yellow-500"
                                  : topic.mastery_score > 0
                                  ? "bg-red-500"
                                  : "bg-gray-200"
                              }`}
                              style={{
                                width: `${Math.min(topic.mastery_score, 100)}%`,
                              }}
                            ></div>
                          </div>
                        </div>
                        <div className="flex items-center gap-3">
                          <MasteryBadge
                            score={
                              topic.attempts_count > 0
                                ? topic.mastery_score
                                : null
                            }
                            size="sm"
                          />
                          <button
                            onClick={() =>
                              navigate(`/quiz/${topic.topic_id}`)
                            }
                            className="text-xs px-2.5 py-1 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 transition-colors"
                          >
                            Quiz
                          </button>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              );
            })}
          </div>

          {/* Sidebar recommendations */}
          <div>
            <h3 className="text-lg font-semibold text-gray-900 mb-4">
              Focus Areas
            </h3>
            {recommendations.length === 0 ? (
              <p className="text-sm text-gray-400">
                Take some quizzes to get recommendations.
              </p>
            ) : (
              <div className="space-y-3">
                {recommendations.map((r, i) => (
                  <div
                    key={i}
                    className="bg-white rounded-xl border border-gray-200 p-4"
                  >
                    <p className="text-sm font-medium text-gray-900">
                      {r.topic_title}
                    </p>
                    <p className="text-xs text-gray-400 mt-0.5">
                      {r.module_title}
                    </p>
                    <p className="text-xs text-gray-500 mt-1">{r.reason}</p>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
