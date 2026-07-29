import api from "./client";

export async function submitFeedback(data: {
  content_type: string;
  content_id: number;
  reason: string;
  comment?: string;
}) {
  const res = await api.post("/feedback", data);
  return res.data;
}
