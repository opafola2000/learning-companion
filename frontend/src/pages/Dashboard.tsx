import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { listCurricula, generateCurriculum } from "../api/curriculum";
import { getRecommendations } from "../api/progress";
import LoadingSpinner from "../components/LoadingSpinner";
import { formatApiError } from "../utils/apiError";

interface CurriculumItem {
  id: number;
  skill_name: string;
  description: string | null;
  created_at: string;
  module_count: number;
  topic_count: number;
  overall_mastery: number;
}

interface Recommendation {
  topic_id: number;
  topic_title: string;
  module_title: string;
  current_mastery: number;
  recommendation_type: string;
  reason: string;
}

export default function Dashboard() {
  const [curricula, setCurricula] = useState<CurriculumItem[]>([]);
  const [recommendations, setRecommendations] = useState<Recommendation[]>([]);
  const [skillName, setSkillName] = useState("");
  const [generating, setGenerating] = useState(false);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const navigate = useNavigate();

  useEffect(() => {
    loadData();
  }, []);

  async function loadData() {
    setError("");
    const errors: string[] = [];

    try {
      const currData = await listCurricula();
      setCurricula(currData);
    } catch (err: unknown) {
      errors.push(formatApiError(err, "Could not load learning paths"));
    }

    try {
      const recData = await getRecommendations();
      setRecommendations(recData);
    } catch (err: unknown) {
      errors.push(formatApiError(err, "Could not load recommendations"));
    }

    if (errors.length > 0) {
      setError(errors.join(" "));
    }
    setLoading(false);
  }

  async function handleGenerate(e: React.FormEvent) {
    e.preventDefault();
    if (!skillName.trim()) return;
    setGenerating(true);
    setError("");
    try {
      const curriculum = await generateCurriculum(skillName.trim());
      navigate(`/curriculum/${curriculum.id}`);
    } catch (err: any) {
      setError(err.response?.data?.detail || "Failed to generate curriculum");
      setGenerating(false);
    }
  }

  if (loading) return <LoadingSpinner />;

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      {/* Skill input */}
      <div className="bg-white rounded-2xl shadow-sm border border-gray-200 p-8 mb-8">
        <h2 className="text-2xl font-bold text-gray-900 mb-2">
          Start Learning a New Skill
        </h2>
        <p className="text-gray-500 mb-6">
          Enter a professional certification or skill, and we'll build a
          personalized curriculum for you.
        </p>
        <form onSubmit={handleGenerate} className="flex gap-4">
          <input
            type="text"
            value={skillName}
            onChange={(e) => setSkillName(e.target.value)}
            placeholder="e.g., AWS Certified AI Practitioner, PMP, CISSP..."
            disabled={generating}
            className="flex-1 px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 outline-none transition-shadow text-lg"
          />
          <button
            type="submit"
            disabled={generating || !skillName.trim()}
            className="px-8 py-3 bg-indigo-600 text-white rounded-lg font-medium hover:bg-indigo-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors whitespace-nowrap"
          >
            {generating ? "Generating..." : "Generate Curriculum"}
          </button>
        </form>
        {generating && (
          <div className="mt-4 flex items-center gap-3 text-indigo-600">
            <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-indigo-600"></div>
            <span>Searching exam guides and building your personalized curriculum... This may take a moment.</span>
          </div>
        )}
        {error && (
          <div className="mt-4 bg-red-50 border border-red-200 text-red-700 rounded-lg p-3 text-sm">
            {error}
          </div>
        )}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Curricula list */}
        <div className="lg:col-span-2">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">
            Your Learning Paths
          </h3>
          {curricula.length === 0 ? (
            <div className="bg-white rounded-xl border border-gray-200 p-8 text-center text-gray-400">
              No curricula yet. Enter a skill above to get started!
            </div>
          ) : (
            <div className="space-y-4">
              {curricula.map((c) => (
                <button
                  key={c.id}
                  onClick={() => navigate(`/curriculum/${c.id}`)}
                  className="w-full text-left bg-white rounded-xl border border-gray-200 p-6 hover:border-indigo-300 hover:shadow-md transition-all"
                >
                  <div className="flex justify-between items-start">
                    <div>
                      <h4 className="text-lg font-semibold text-gray-900">
                        {c.skill_name}
                      </h4>
                      <p className="text-sm text-gray-500 mt-1">
                        {c.module_count} modules, {c.topic_count} topics
                      </p>
                    </div>
                    <div className="text-right">
                      <div className="text-2xl font-bold text-indigo-600">
                        {Math.round(c.overall_mastery)}%
                      </div>
                      <div className="text-xs text-gray-400">mastery</div>
                    </div>
                  </div>
                  {/* Progress bar */}
                  <div className="mt-4 w-full bg-gray-100 rounded-full h-2">
                    <div
                      className="bg-indigo-600 h-2 rounded-full transition-all"
                      style={{ width: `${Math.min(c.overall_mastery, 100)}%` }}
                    ></div>
                  </div>
                </button>
              ))}
            </div>
          )}
        </div>

        {/* Recommendations */}
        <div>
          <h3 className="text-lg font-semibold text-gray-900 mb-4">
            Recommended Next Steps
          </h3>
          {recommendations.length === 0 ? (
            <div className="bg-white rounded-xl border border-gray-200 p-6 text-center text-gray-400 text-sm">
              Generate a curriculum and take some quizzes to get personalized recommendations.
            </div>
          ) : (
            <div className="space-y-3">
              {recommendations.slice(0, 5).map((r, i) => (
                <div
                  key={i}
                  className="bg-white rounded-xl border border-gray-200 p-4"
                >
                  <div className="flex items-start gap-3">
                    <span
                      className={`mt-0.5 flex-shrink-0 w-6 h-6 rounded-full flex items-center justify-center text-xs font-bold text-white ${
                        r.recommendation_type === "review"
                          ? "bg-red-500"
                          : r.recommendation_type === "start"
                          ? "bg-blue-500"
                          : r.recommendation_type === "practice"
                          ? "bg-yellow-500"
                          : "bg-green-500"
                      }`}
                    >
                      {i + 1}
                    </span>
                    <div>
                      <p className="text-sm font-medium text-gray-900">
                        {r.topic_title}
                      </p>
                      <p className="text-xs text-gray-400">{r.module_title}</p>
                      <p className="text-xs text-gray-500 mt-1">{r.reason}</p>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
