import api from "./client";

export async function getCurriculumProgress(curriculumId: number) {
  const res = await api.get(`/progress/${curriculumId}`);
  return res.data;
}

export async function getRecommendations() {
  const res = await api.get("/progress/recommendations");
  return res.data;
}

export async function searchResources(topicId: number) {
  const res = await api.post(`/resources/search/${topicId}`);
  return res.data;
}

export async function getResources(topicId: number) {
  const res = await api.get(`/resources/${topicId}`);
  return res.data;
}
