import { useState, useEffect } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { getCurriculum } from "../api/curriculum";
import { searchResources, getResources } from "../api/progress";
import LoadingSpinner from "../components/LoadingSpinner";
import MasteryBadge from "../components/MasteryBadge";

interface AnswerOption {
  id: number;
  option_text: string;
}

interface Question {
  id: number;
  question_text: string;
  difficulty: string;
  options: AnswerOption[];
}

interface Topic {
  id: number;
  title: string;
  description: string | null;
  difficulty: string;
  status: string;
  mastery_score: number | null;
}

interface Module {
  id: number;
  title: string;
  description: string | null;
  order_index: number;
  topics: Topic[];
}

interface Curriculum {
  id: number;
  skill_name: string;
  description: string | null;
  created_at: string;
  modules: Module[];
}

interface Resource {
  id: number;
  title: string;
  url: string;
  type: string;
  summary: string | null;
}

export default function CurriculumView() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [curriculum, setCurriculum] = useState<Curriculum | null>(null);
  const [expandedModule, setExpandedModule] = useState<number | null>(null);
  const [expandedTopic, setExpandedTopic] = useState<number | null>(null);
  const [resources, setResources] = useState<Record<number, Resource[]>>({});
  const [loadingResources, setLoadingResources] = useState<number | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (id) {
      getCurriculum(parseInt(id))
        .then((data) => {
          setCurriculum(data);
          if (data.modules.length > 0) {
            setExpandedModule(data.modules[0].id);
          }
        })
        .catch(() => navigate("/"))
        .finally(() => setLoading(false));
    }
  }, [id, navigate]);

  async function handleLoadResources(topicId: number) {
    if (resources[topicId]) {
      setExpandedTopic(expandedTopic === topicId ? null : topicId);
      return;
    }

    setLoadingResources(topicId);
    setExpandedTopic(topicId);
    try {
      let res = await getResources(topicId);
      if (res.length === 0) {
        res = await searchResources(topicId);
      }
      setResources((prev) => ({ ...prev, [topicId]: res }));
    } catch {
      // ignore
    } finally {
      setLoadingResources(null);
    }
  }

  if (loading || !curriculum) return <LoadingSpinner />;

  return (
    <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      {/* Header */}
      <div className="mb-8">
        <button
          onClick={() => navigate("/")}
          className="text-sm text-indigo-600 hover:underline mb-2 inline-block"
        >
          &larr; Back to Dashboard
        </button>
        <h1 className="text-3xl font-bold text-gray-900">
          {curriculum.skill_name}
        </h1>
        {curriculum.description && (
          <p className="text-gray-500 mt-2 text-lg">{curriculum.description}</p>
        )}
      </div>

      {/* Modules */}
      <div className="space-y-4">
        {curriculum.modules.map((module, modIdx) => (
          <div
            key={module.id}
            className="bg-white rounded-xl border border-gray-200 overflow-hidden"
          >
            <button
              onClick={() =>
                setExpandedModule(
                  expandedModule === module.id ? null : module.id
                )
              }
              className="w-full text-left p-6 flex justify-between items-center hover:bg-gray-50 transition-colors"
            >
              <div className="flex items-center gap-4">
                <span className="w-8 h-8 rounded-full bg-indigo-100 text-indigo-600 flex items-center justify-center font-bold text-sm">
                  {modIdx + 1}
                </span>
                <div>
                  <h3 className="text-lg font-semibold text-gray-900">
                    {module.title}
                  </h3>
                  {module.description && (
                    <p className="text-sm text-gray-500">{module.description}</p>
                  )}
                </div>
              </div>
              <div className="flex items-center gap-3">
                <span className="text-sm text-gray-400">
                  {module.topics.length} topics
                </span>
                <svg
                  className={`w-5 h-5 text-gray-400 transition-transform ${
                    expandedModule === module.id ? "rotate-180" : ""
                  }`}
                  fill="none"
                  viewBox="0 0 24 24"
                  stroke="currentColor"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M19 9l-7 7-7-7"
                  />
                </svg>
              </div>
            </button>

            {expandedModule === module.id && (
              <div className="border-t border-gray-100 px-6 pb-4">
                {module.topics.map((topic) => (
                  <div key={topic.id} className="py-4 border-b border-gray-50 last:border-0">
                    <div className="flex justify-between items-center">
                      <div className="flex-1">
                        <div className="flex items-center gap-3">
                          <h4 className="font-medium text-gray-900">
                            {topic.title}
                          </h4>
                          <span
                            className={`text-xs px-2 py-0.5 rounded-full ${
                              topic.difficulty === "advanced"
                                ? "bg-red-50 text-red-600"
                                : topic.difficulty === "intermediate"
                                ? "bg-yellow-50 text-yellow-600"
                                : "bg-green-50 text-green-600"
                            }`}
                          >
                            {topic.difficulty}
                          </span>
                        </div>
                        {topic.description && (
                          <p className="text-sm text-gray-500 mt-1">
                            {topic.description}
                          </p>
                        )}
                      </div>
                      <div className="flex items-center gap-3 ml-4">
                        <MasteryBadge score={topic.mastery_score} size="sm" />
                        <button
                          onClick={() => navigate(`/quiz/${topic.id}`)}
                          className="text-sm px-3 py-1.5 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 transition-colors"
                        >
                          Quiz
                        </button>
                        <button
                          onClick={() => handleLoadResources(topic.id)}
                          className="text-sm px-3 py-1.5 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 transition-colors"
                        >
                          Resources
                        </button>
                      </div>
                    </div>

                    {/* Resources section */}
                    {expandedTopic === topic.id && (
                      <div className="mt-3 ml-4 p-4 bg-gray-50 rounded-lg">
                        {loadingResources === topic.id ? (
                          <div className="flex items-center gap-2 text-sm text-gray-500">
                            <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-indigo-600"></div>
                            Searching for resources...
                          </div>
                        ) : resources[topic.id]?.length > 0 ? (
                          <ul className="space-y-3">
                            {resources[topic.id].map((r) => (
                              <li key={r.id}>
                                <a
                                  href={r.url}
                                  target="_blank"
                                  rel="noopener noreferrer"
                                  className="text-sm font-medium text-indigo-600 hover:underline"
                                >
                                  {r.title}
                                </a>
                                <span className="ml-2 text-xs px-2 py-0.5 rounded-full bg-gray-200 text-gray-600">
                                  {r.type}
                                </span>
                                {r.summary && (
                                  <p className="text-xs text-gray-500 mt-0.5">
                                    {r.summary}
                                  </p>
                                )}
                              </li>
                            ))}
                          </ul>
                        ) : (
                          <p className="text-sm text-gray-400">
                            No resources found.
                          </p>
                        )}
                      </div>
                    )}
                  </div>
                ))}
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}
