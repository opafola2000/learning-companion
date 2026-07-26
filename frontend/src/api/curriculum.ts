import api from "./client";

export async function listCurricula() {
  const res = await api.get("/curriculum");
  return res.data;
}

export async function generateCurriculum(skillName: string) {
  const res = await api.post("/curriculum/generate", {
    skill_name: skillName,
  });
  return res.data;
}

export async function getCurriculum(id: number) {
  const res = await api.get(`/curriculum/${id}`);
  return res.data;
}
